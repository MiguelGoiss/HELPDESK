from functools import reduce
from operator import or_
from app.database.models.helpdesk import Tickets, TicketLogs, TicketAttachments, Employees
from app.services.users import get_users_by_ids, get_employee_basic_info
from app.utils.errors.exceptions import CustomError
from app.services.emails.emails import ticket_email
from app.utils.helpers.paginate import paginate
from datetime import datetime, timedelta
from app.services.logs import LogService
from tortoise.expressions import Q
# from tortoise import connections
from tortoise.transactions import in_transaction
from fastapi import UploadFile
from pathlib import Path
import aiofiles
import os
import uuid
import time

# --- Configurações de criação de ticket ---
TICKET_FILES_PATH = os.getenv('TICKET_FILES_PATH')

# Define onde os uploads vão ser guardados.
UPLOAD_DIRECTORY = Path(TICKET_FILES_PATH)
# Garante que a pasta existe
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
# Extensões de ficheiros permitidas
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".pdf", ".msg"}
# --- Fim da Configuração ---

# --- Inicio da criação do ticket ---
async def create_ticket(
  ticket_data: dict,
  current_user: dict,
  files: list[UploadFile] | None = None
  ):
  new_ticket_orm = None
  ticket_log_details_filtered = {}
  ccs_ids_to_add = None
  
  # Os campos de equipments e suppliers têm de ser enviado em JSON encriptado fazendo JSON.parse()
  async with in_transaction('helpdesk') as conn:
    try:
      # --- Inicia a transação ---
      # Prepara os dados do ticket
      ticket_dict = ticket_data.dict(exclude_none=True)
      ccs_ids_to_add = ticket_dict.pop('ccs', None)
      
      if current_user:
        ticket_dict['created_by_id'] = current_user['id']

      ticket_dict['created_at'] = datetime.now()

      # Criar o ticket
      new_ticket_orm = await Tickets()._create_ticket(**ticket_dict)

      # Log da criação do ticket
      ticket_log_details = await new_ticket_orm.to_dict_log()
      ticket_log_details_filtered = {
        key: value
        for key, value in ticket_log_details.items()
        if value is not None
      }
      await LogService.log_action(
        "Criado",
        current_user['id'] if current_user else new_ticket_orm.requester_id,
        TicketLogs,
        new_ticket_orm.id,
        None,
        ticket_log_details_filtered
      )
      
      if ccs_ids_to_add:
        await handle_ticket_creation_ccs(ccs_ids_to_add, new_ticket_orm)

      # Lida com os uploads de ficheiros, guarda e adiciona à DB
      if files:
        # Qualquer exceção que ocorre dentro de handle_file_uploads vai abortar a transação
        await handle_file_uploads(new_ticket_orm, files)

      # --- A transação insere todos os dados se não foi levantada nenhuma exceção ---
      updated_ticket_details = await new_ticket_orm.to_dict_log()
    except CustomError as e:
      raise e
    
    except Exception as e:
      # Se ocorrer algum erro o Tortoise vai dar roll back na transação.
      print(f"Error during transaction, rollback initiated: {e}")
      raise CustomError(500, "Ocorreu um erro durante a criação do ticket ou processamento de anexos", str(e)) from e

  # Envia o email de confirmação para o cliente com técnico (se houver) e os utilizadores selecionados como ccs em cc
  try:
    await handle_ticket_emails(new_ticket_orm, updated_ticket_details, "create")
  except Exception as email_error:
    raise CustomError(
      500,
      "Ocorreu um erro a enviar o email",
      str(email_error)
    )

  updated_ticket_details.pop("uid")
  return updated_ticket_details

async def handle_ticket_emails(ticket: Tickets, ticket_info: dict, email_type: str | None = None):
  try:
    requester_info = await get_employee_basic_info(ticket.requester_id)
    agent_info = await get_employee_basic_info(ticket.agent_id)
    await ticket_email(ticket_info, requester_info, agent_info, email_type) 

  except CustomError as e:
    raise e
  
  except Exception as e:
    raise CustomError(
      500,
      "Ocorreu um erro a enviar o email",
      str(e)
    ) from e
  
async def handle_ticket_creation_ccs(ccs_ids: list[int], new_ticket: Tickets):
  if not ccs_ids:
    return

  try:
    # Obtem os objetos dos colaboradores para os ids inseridos, using the transaction connection
    ccs_employees_to_add = await get_users_by_ids(ccs_ids)

    # Adiciona os colaboradores obtidos na many-to-many
    if ccs_employees_to_add:
      # This operation uses the connection implicitly via the new_ticket object
      await new_ticket.ccs.add(*ccs_employees_to_add)
      print(f"Successfully added {len(ccs_employees_to_add)} employees to CCS for ticket {new_ticket.id}")

  except Exception as e:
    print(f"Error adding CCS to ticket {new_ticket.id}: {e}")
    # Raise a specific error to ensure transaction rollback
    raise CustomError(500, f"Failed to add CCS employees to ticket {new_ticket.id}", str(e)) from e

async def handle_file_uploads(ticket: Tickets, files: list[UploadFile]):
  attachment_records_data = []
  saved_file_paths = []
  try:
    if files:
      date_now = datetime.now()
      for file in files:
        if not file or not file.filename:
          continue

        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
          raise CustomError(400, "Ocorreu um erro a inserir um fichiero. O ticket não foi criado.", f"Tipo de ficheiro não permitido: {file.filename}, apenas são permitidas as seguintes extensões: {', '.join(ALLOWED_EXTENSIONS)}")
        
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        date_save_path = UPLOAD_DIRECTORY / date_now.strftime("%Y/%m/%d")
        date_save_path.mkdir(parents=True, exist_ok=True)
        save_path = date_save_path / unique_filename 

        try:
          # Guarda o ficheiro async
          async with aiofiles.open(save_path, 'wb') as out_file:
            while content := await file.read(1024 * 1024): # Lê o ficheiro aos "pedaços"
              await out_file.write(content)
          saved_file_paths.append(save_path) # Adiciona o ficheiro adicionado à lista

          # Prepara os dados do ficheiro para a DB
          attachment_data = {
            "filename": unique_filename,
            "original_name": file.filename,
            "extension": file_ext,
            "ticket_id": ticket.id,
            "agent_id": ticket.agent_id
          }
          attachment_records_data.append(attachment_data)

        except Exception as save_error:
          # CRITICO: Se guardar um ficheiro falhar, abortar a transação com um erro
          raise CustomError(500, f"Erro ao guardar o ficheiro: {file.filename}", str(save_error)) from save_error
        finally:
          # Garante que os ficheiros estão fechados
          if file:
            await file.close()
          
          if saved_file_paths:
            await LogService.log_action(
              f"Adicionou {len(saved_file_paths)} anexo(s)",
              ticket.requester_id,
              TicketLogs,
              ticket.id,
              None,
              attachment_records_data
            )

    # Bulk create dos ficheiros
    if attachment_records_data:
      try:
        # Esta operação é parte da transação iniciada no create_ticket
        await TicketAttachments.bulk_create([TicketAttachments(**data) for data in attachment_records_data])
      except Exception as db_error:
        # CRÍTICO: A operação falhou a transação será revertida
        # Tenta limpar os ficheiros guardados no disco durante esta função
        for path in saved_file_paths:
          try:
            if path.is_file(): # Check if it exists and is a file before removing
              os.remove(path)
          except OSError as cleanup_error:
            # Log cleanup error but proceed to raise the main DB error
            print(f"Error cleaning up file {path}: {cleanup_error}")
        # Raise an error to ensure the transaction rollback is triggered correctly by the caller.
        raise CustomError(500, "Erro ao guardar anexos na base de dados", str(db_error)) from db_error

  except CustomError as e:
    raise e
  
  except Exception as e:
    raise CustomError(500, "Erro inesperado no processamento de ficheiros", str(e)) from e

# --- Fim da criação do ticket ---

# --- Inicio do get de todos os tickets ---
# --- Configuração: Definição de campos disponíveis para pesquisa e order ---

# Campos que suportam filtros entre datas.
DATE_FIELDS: set[str] = {
  'prevention_date',
  'created_at',
  'closed_at',
}

# Campos permitidos para a pesquisa geral 'search' (OR) - Adjust as needed
DEFAULT_OR_SEARCH_FIELDS: list[str] = [
  'id',
  'uid',
  'subject',
  'request',
  'response',
  'internal_comment',
  'supplier_reference',
  'requester__first_name',
  'requester__last_name',
  'requester__full_name',
  'agent__first_name',
  'agent__last_name',
  'agent__full_name',
  'company__name',
  'category__name',
  'subcategory__name',
]

# Campos permitidos para a pesquisa específica (AND)
ALLOWED_AND_FILTER_FIELDS: set[str] = {
  # Campos diretos
  'id',
  'uid',
  'subject',
  'request',
  'response',
  'internal_comment',
  'supplier_reference',
  'spent_time',
  'prevention_date',
  'created_at',
  'closed_at',
  # Foreign Key IDs
  'company_id',
  'category_id',
  'subcategory_id',
  'status_id',
  'type_id',
  'priority_id',
  'assistance_type_id',
  'requester_id',
  'agent_id',
  # Atributos relacionados
  'company__name',
  'category__name',
  'subcategory__name',
  'status__name',
  'type__name',
  'priority__name',
  'assistance_type__name',
  'requester__username',
  'requester__email',
  'requester__first_name',
  'requester__last_name',
  'requester__full_name',
  'requester__department__name',
  'requester__department__id'
  'agent__username',
  'agent__email',
  'agent__first_name',
  'agent__last_name',
  'agent__full_name',
}

# Campos permitidos para order
ALLOWED_ORDER_FIELDS: set[str] = {
  # Campos diretos
  'id',
  'uid',
  'subject',
  # Datas
  'created_at',
  'closed_at',
  # Foreign Key IDs
  'company_id',
  'category_id',
  'subcategory_id',
  'status_id',
  'type_id',
  'priority_id',
  'assistance_type_id',
  'requester_id',
  'agent_id',
  # Atributos relacionados
  'company__name',
  'category__name',
  'subcategory__name',
  'status__name',
  'type__name',
  'priority__name',
  'assistance_type__name',
  'requester__full_name',
  'agent__full_name',
}
# --- Fim da Configuração ---

async def fetch_tickets(
  path: str,
  page: int,
  page_size: int,
  original_query_params: dict | None = None,
  # O parametro search serve para pesquisa geral (OR)
  search: str | None = None,
  # Dict para pesquisa especifica (AND)
  and_filters: dict[str, any] | None = None,
  # Campos para ordenação, usar o prefixo '-' para descendente
  order_by: str | None = None
  ) -> dict:
  start = time.time()
  queryset = Tickets.all()
  # Filtros para o search (AND)
  if and_filters:
    valid_and_filters = {}
    for field, value in and_filters.items():
      # --- Filtro de datas ---
      # Para a pesquisa de datas os campos devem vir e.g. "prevention_date_after" para a data de inicio e "prevention_date_before" para a data de fim
      if field.endswith('_after'):
        base_field = field[:-6] # Remove o '_after'
        if base_field in DATE_FIELDS:
          try:
            start_date = datetime.fromisoformat(str(value)).date()
            filter_key = f"{base_field}__gte"
            valid_and_filters[filter_key] = datetime.combine(start_date, datetime.min.time())
            continue
          except ValueError:
            raise CustomError(400, "Formato de data inválido", f"Formato inválido para '{field}'. Usar YYYY-MM-DD.")
        else:
          raise CustomError(400, "Filtro inválido", f"Não é possível filtrar por data no campo '{base_field}'.")

      elif field.endswith('_before'):
        base_field = field[:-7] # Remove o '_before'
        if base_field in DATE_FIELDS:
          try:
            end_date = datetime.fromisoformat(str(value)).date()
            next_day_start = datetime.combine(end_date + timedelta(days=1), datetime.min.time())
            filter_key = f"{base_field}__lt"
            valid_and_filters[filter_key] = next_day_start
            continue
          except ValueError:
            raise CustomError(400, "Formato de data inválido", f"Formato inválido para '{field}'. Usar YYYY-MM-DD.")
        else:
          raise CustomError(400, "Filtro inválido", f"Não é possível filtrar por data no campo '{base_field}'.")
      
      # --- Filtro de campos que não são datas ---
      if field in ALLOWED_AND_FILTER_FIELDS:
        if isinstance(value, str) and not field.endswith('_id'):
          filter_key = f"{field}__icontains"
          valid_and_filters[filter_key] = value
        elif isinstance(value, list):
          filter_key = f"{field}__in"
          valid_and_filters[filter_key] = value
        else:
          valid_and_filters[field] = value
      else:
        raise CustomError(400, "Filtro inválido", f"Não é possível filtrar pelo campo '{field}'.")

    if valid_and_filters:
      queryset = queryset.filter(**valid_and_filters)

  # Aplica search geral (OR)
  if search:
    search_conditions = []
    for field in DEFAULT_OR_SEARCH_FIELDS:
      if field == 'id' and search.isdigit():
        search_conditions.append(Q(id=int(search)))
      else:
        filter_key = f"{field}__icontains"
        search_conditions.append(Q(**{filter_key: search}))

    if search_conditions:
      # Combina todas as condições (OR)
      combined_condition = reduce(or_, search_conditions)
      queryset = queryset.filter(combined_condition)
    else:
      queryset = queryset.none()

  # Aplica o order
  if order_by:
    order_field_name = order_by.lstrip('-') # Retira o '-' se houver
    if order_field_name in ALLOWED_ORDER_FIELDS:
      queryset = queryset.order_by(order_by)
    else:
      raise CustomError(400, "Ordenação inválida", f"Ordenação pelo campo '{order_field_name}' não é permitida.")
  else:
    # Por defeito o order é pela data de criação
    queryset = queryset.order_by('-created_at')

  queryset = queryset.prefetch_related(
    'status',
    'priority',
    'category',
    'requester',
    'agent',
    'attachments'
  )

  # Helper de paginação
  try:
    paginated_result = await paginate(
      queryset=queryset,
      url=path,
      page=page,
      page_size=page_size,
      original_query_params=original_query_params
    )
  except Exception as e:
    raise CustomError(500, "Erro ao processar a lista de tickets.", str(e)) from e


  end = time.time()
  print(f"fetch_tickets execution time: {end-start:.4f}s")
  return paginated_result

# --- Fim do get de todos os tickets ---

# --- Inicio do get dos detalhes de um ticket pelo uid ---
  
async def fetch_ticket_details(uid: str) -> dict:
  try:
    ticket = await Tickets.get_or_none(uid=uid).prefetch_related(
      'status',
      'priority',
      'category',
      'subcategory',
      'requester',
      'agent',
      'company',
      'ccs',
      'attachments',
      'type',
      'assistance_type',
      'created_by'  
    )

    # Check if the ticket was found
    if not ticket:
      raise CustomError(404, "Ticket não encontrado", f"Nenhum ticket encontrado com o UID: {uid}")

    # Serialize the ticket details using the specified method
    ticket_details = await ticket.to_dict_details()
    return ticket_details

  except CustomError as e:
    raise e
  
  except Exception as e:
    raise CustomError(500, "Erro ao buscar detalhes do ticket", str(e)) from e

# --- Fim do get dos detalhes de um ticket pelo uid ---

# --- Inicio da atualização de um ticket ---

async def update_ticket_details(
    uid: str,
    ticket_data: dict,
    current_user: dict,
    files: list[UploadFile] | None = None
    ) -> dict:
  if not current_user or 'id' not in current_user or 'permissions' not in current_user:
    raise CustomError(401, "Não autenticado", "Informações do utilizador atual inválidas ou ausentes.")

  async with in_transaction('helpdesk') as conn:
    try:
      # 1. Fetch the ticket and necessary relations
      ticket = await Tickets.get_or_none(uid=uid).prefetch_related(
        'status', 'priority', 'category', 'subcategory', 'requester',
        'agent', 'company', 'ccs', 'type', 'assistance_type', 'created_by'
      )
      if not ticket:
        raise CustomError(404, "Ticket não encontrado", f"Nenhum ticket encontrado com o UID: {uid}")

      # 2. Authorization Check (Agent or 'tecnico')
      user_id = current_user['id']
      user_permissions = current_user.get('permissions', [])
      # is_agent = (ticket.agent_id == user_id)
      has_tecnico_permission = ('tecnico' in user_permissions) # Adjust permission name if needed

      if not has_tecnico_permission: # not is_agent and
        raise CustomError(403, "Acesso negado", "Você não tem permissão para editar este ticket.")

      # 3. Get old state for logging
      old_ticket_details = await ticket.to_dict_log()

      # 4. Prepare update data
      update_data = ticket_data.dict(exclude_unset=True, exclude_none=True)
      ccs_ids_to_update = update_data.pop('ccs', None)

      # Previne alterar campos que não devem ser alterados
      protected_fields = ['id', 'uid', 'created_at', 'created_by_id', 'requester_id']
      for field in protected_fields:
        update_data.pop(field, None)

      # 5. Apply updates to the ticket object
      status_changed_to_closed = False
      for key, value in update_data.items():
        if hasattr(ticket, key):
          # Check if status is changing to a 'closed' status (assuming ID 4 is closed)
          if key == 'status_id' and getattr(ticket, key) != value and value == 4: # Adjust '4' if your closed status ID is different
            status_changed_to_closed = True
          setattr(ticket, key, value)
        else:
          print(f"Warning: Attempted to update non-existent field '{key}' on ticket {uid}") # Or raise error

      # Update closed_at if status changed to closed
      if status_changed_to_closed and not ticket.closed_at:
        ticket.closed_at = datetime.now()
      elif 'status_id' in update_data and update_data['status_id'] != 4 and ticket.closed_at:
        # If reopening, clear closed_at (optional behavior)
        ticket.status_id = 2 # Alterar para id de reaberto?
        ticket.closed_at = None

      # 6. Handle CCS updates (replace existing CCS with new list)
      if ccs_ids_to_update is not None: # Allow empty list to clear CCS
        ccs_employees = await get_users_by_ids(ccs_ids_to_update) if ccs_ids_to_update else []
        await ticket.ccs.clear() # Remove existing
        if ccs_employees:
          await ticket.ccs.add(*ccs_employees) # Add new ones

      # 7. Handle file uploads (if any) - uses the existing handle_file_uploads function
      if files:
        await handle_file_uploads(ticket, files)

      # 8. Save the changes
      await ticket.save()

      # 9. Log the changes
      new_ticket_details = await ticket.to_dict_log()
      # Filter details to only include changed fields for the log description
      changed_details = {k: new_ticket_details[k] for k in new_ticket_details if k in old_ticket_details and new_ticket_details[k] != old_ticket_details[k]}
      # Adiciona ccs ao log
      if ccs_ids_to_update is not None:
        changed_details['ccs'] = f"Updated to IDs: {ccs_ids_to_update}"

      await LogService.log_action(
        "Atualizado",
        current_user['id'],
        TicketLogs,
        ticket.id,
        old_ticket_details,
        changed_details
      )

      # --- Transaction commits here if no exceptions ---

    except CustomError as e:
      raise e
    except Exception as e:
      print(f"Error during ticket update transaction for UID {uid}, rollback initiated: {e}")
      raise CustomError(500, "Ocorreu um erro ao atualizar o ticket", str(e)) from e

  # --- Post-Transaction Actions (e.g., Email Notifications) ---
  try:
    # Decide if email needs to be sent based on changes (e.g., response added, status changed)
    if 'response' in changed_details or 'status_id' in changed_details: # Example condition
      # Fetch fresh details if needed, or use new_ticket_details if sufficient
      final_details = await ticket.to_dict_details() # Use detailed view for email
      await handle_ticket_emails(ticket, final_details, "update")
  except Exception as email_error:
    # Log email error but don't fail the whole request as the update succeeded
    print(f"Failed to send update email for ticket UID {uid}: {email_error}")
    # Optionally, you could return a warning in the response

  # Return the final state of the ticket
  return await ticket.to_dict_details() # Return detailed view

# --- Fim da atualização de um ticket ---

    

