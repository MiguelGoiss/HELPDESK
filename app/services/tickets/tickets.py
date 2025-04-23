from app.database.models.helpdesk import Tickets, TicketLogs, TicketAttachments, Employees
from app.services.users import get_users_by_ids, get_employee_basic_info
from app.utils.errors.exceptions import CustomError
from app.services.emails.emails import ticket_email
from app.utils.helpers.paginate import paginate
from datetime import datetime
from app.services.logs import LogService
from tortoise.expressions import Q
# from tortoise import connections
from tortoise.transactions import in_transaction
from fastapi import UploadFile
from pathlib import Path
import aiofiles
import os
import uuid


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
# Campos permitidos para a pesquisa geral 'search' (OR)

# Campos permitidos para a pesquisa (AND)

# Campos permitidos para order

# --- Fim da Configuração ---

async def fetch_tickets(
  path: str,
  page: int,
  page_size: int,
  original_query_params: dict | None = None,
  # O parametro search serve para pesquisa (OR)
  search: str | None = None,
  # Dict para pesquisa especifica (AND)
  and_filters: dict[str, any] | None = None,
  # Campos para ordenação, usar o prefixo '-' para descendente
  order_by: str | None = None
  ) -> dict:
  

