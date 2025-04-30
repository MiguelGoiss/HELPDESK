from functools import reduce
from operator import or_
from app.database.models.helpdesk import Tickets, TicketLogs
from app.utils.helpers.tickets import (
  _handle_ticket_creation_ccs,
  _handle_file_uploads,
  _handle_ticket_emails,
  _get_ticket_for_update,
  # _authorize_ticket_update,
  _prepare_update_data,
  _apply_direct_updates,
  _handle_automatic_status_update,
  _handle_closed_at_update,
  _handle_ccs_update,
  _handle_update_logging,
  _handle_update_notifications,
)
from app.services.users import get_users_by_ids
from app.utils.errors.exceptions import CustomError
from app.utils.helpers.paginate import paginate
from datetime import datetime, timedelta
from app.services.logs import LogService
from tortoise.expressions import Q
from tortoise.functions import Count
from tortoise.transactions import in_transaction
from fastapi import UploadFile
import time

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
        await _handle_ticket_creation_ccs(ccs_ids_to_add, new_ticket_orm)

      # Lida com os uploads de ficheiros, guarda e adiciona à DB
      if files:
        # Qualquer exceção que ocorre dentro de handle_file_uploads vai abortar a transação
        await _handle_file_uploads(new_ticket_orm, files, current_user)

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
    await _handle_ticket_emails(new_ticket_orm, updated_ticket_details, "create")
  except Exception as email_error:
    raise CustomError(
      500,
      "Ocorreu um erro a enviar o email",
      str(email_error)
    )

  updated_ticket_details.pop("uid")
  return updated_ticket_details

# --- Fim da criação do ticket ---

# --- Inicio do get de todos os tickets ---
# --- Configuração: Definição de campos disponíveis para pesquisa e order ---

# Campos que suportam filtros entre datas.
DATE_FIELDS: set[str] = {
  'prevention_date',
  'created_at',
  'closed_at',
}

# Campos permitidos para a pesquisa geral 'search' (OR) (É uma lista devido a uma iteração que tem de ser feita no search de or)
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
  page_size: int,
  page: int,
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

  # Annotate with the count of attachments instead of fetching all attachment objects
  queryset = queryset.annotate(attachments_count=Count("attachments"))
  
  queryset = queryset.prefetch_related(
    'status',
    'priority',
    'category',
    'subcategory',
    'requester', 
    'requester__department',
    'requester__company',
    'requester__local',
    'requester__employee_relation',
    'agent',
    'agent__department',
    'agent__company',
    'agent__local',
    'agent__employee_relation',
  )

  # Helper de paginação
  try:
    paginated_result = await paginate(
      queryset=queryset,
      url=path,
      page=page,
      page_size=page_size,
      original_query_params=original_query_params,
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

# --- Inicio do update de um ticket pelo uid ---

async def update_ticket_details(
    uid: str,
    ticket_data: dict,
    current_user: dict,
    files: list[UploadFile] | None = None
  ) -> dict:

  ticket = await _get_ticket_for_update(uid)
  # _authorize_ticket_update(ticket, current_user)
  # Guarda o estado do ticket antes de qualquer alteração para logs e comparações
  old_ticket_details = await ticket.to_dict_log()
  original_agent_id_value = ticket.agent_id # Capture the actual ID from the modeloriginal_status_id_value

  # Prepara os dados para o update
  update_data, ccs_ids_to_update = _prepare_update_data(ticket_data)

  assigned = False
  async with in_transaction('helpdesk') as conn:
    try:
      # --- Operações em transação ---
      # Aplica alterações nos campos diretos.
      _apply_direct_updates(ticket, update_data)
      
      # Lida com as alterações automáticas de estado
      assigned = _handle_automatic_status_update(ticket, update_data, original_agent_id_value)
      
      # Lida com o estado "fechado"
      _handle_closed_at_update(ticket, old_ticket_details)
      
      # Lida com o update dos CCS
      await _handle_ccs_update(ticket, ccs_ids_to_update)

      # Lida com upload de ficheiros
      if files:
        await _handle_file_uploads(ticket, files, current_user)

      # Guarda todas as alterações feitas
      await ticket.save()
      
      # Cria log das alterações
      # Atualiza os detalhes atualizados do ticket com uma nova pesquisa na base de dados.
      new_ticket_details = await _get_ticket_for_update(uid)

      # Passa a informação necessária para criar o log
      await _handle_update_logging(
        new_ticket_details,
        old_ticket_details,
        ccs_ids_to_update,
        current_user['id']
      )
      # --- A Transação faz commit se não houver erros ---

    except CustomError as e:
      raise e
    
    except Exception as e:
      print(f"Error during ticket update transaction for UID {uid}, rollback initiated: {e}")
      raise CustomError(500, "Ocorreu um erro ao atualizar o ticket", str(e)) from e
  
  # ---  Notifica o requerente ---
  # Envia email após todas as alterações.
  await _handle_update_notifications(ticket, assigned)

  try:
    updated_ticket_details = await fetch_ticket_details(uid)
    return updated_ticket_details

  except CustomError as e:
    raise e
  
  except Exception as e:
    raise CustomError(500, "Erro ao obter detalhes atualizados do ticket após a atualização.", str(e)) from e

# --- Fim da atualização de um ticket ---


    

