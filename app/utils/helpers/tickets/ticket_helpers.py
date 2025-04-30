from app.database.models.helpdesk import Tickets, TicketLogs, TicketAttachments, Employees
from app.services.users import get_users_by_ids, get_employee_basic_info
from app.services.emails.emails import ticket_email
from app.utils.errors.exceptions import CustomError
from datetime import datetime
from app.services.logs import LogService
from fastapi import UploadFile
from pathlib import Path
import aiofiles
import os
import uuid

# --- Helper para adicionar ccs na criação do ticket ---
async def _handle_ticket_creation_ccs(ccs_ids: list[int], new_ticket: Tickets):
  if not ccs_ids:
    return

  try:
    # Obtem os objetos dos colaboradores para os ids inseridos, using the transaction connection
    ccs_employees_to_add = await get_users_by_ids(ccs_ids)

    # Adiciona os colaboradores obtidos na many-to-many
    if ccs_employees_to_add:
      # This operation uses the connection implicitly via the new_ticket object
      await new_ticket.ccs.add(*ccs_employees_to_add)

  except Exception as e:
    raise CustomError(500, f"Ocorreu um erro ao adicionar CCS ao ticket {new_ticket.id}", str(e)) from e
  
# --- Fim do Helper para adicionar ccs na criação do ticket ---

# --- Helper de Upload de Ficheiros ---
# --- Configurações para adicionar ficheiros ---
TICKET_FILES_PATH = os.getenv('TICKET_FILES_PATH')
# Define onde os uploads vão ser guardados
UPLOAD_DIRECTORY = Path(TICKET_FILES_PATH)
# Garante que a pasta existe
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
# Extensões de ficheiros permitidas
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".pdf", ".msg"}
# --- Fim da Configuração ---

def _validate_file(file: UploadFile):
  """Valida os ficheiros inseridos e verifica as suas extensões."""
  if not file or not file.filename:
    # Da skip  do ficheiro se não for válido ou estiver vazio
    return False, None # Indica para dar skip, não é necessário dar raise num erro

  file_ext = Path(file.filename).suffix.lower()
  if file_ext not in ALLOWED_EXTENSIONS:
    error_msg = f"Tipo de ficheiro não permitido: {file.filename}, apenas são permitidas as seguintes extensões: {', '.join(ALLOWED_EXTENSIONS)}"
    raise CustomError(400, "Ocorreu um erro a inserir um ficheiro.", error_msg)
  return True, file_ext

def _generate_save_path(file_ext: str) -> tuple[Path, str]:
  """Gera um filename único e o path para guardar."""
  unique_filename = f"{uuid.uuid4()}{file_ext}"
  # Use current date for directory structure
  date_now = datetime.now()
  date_save_path = UPLOAD_DIRECTORY / date_now.strftime("%Y/%m/%d")
  date_save_path.mkdir(parents=True, exist_ok=True)
  save_path = date_save_path / unique_filename
  return save_path, unique_filename

async def _save_file_to_disk(file: UploadFile, save_path: Path):
  """Guarda o ficheiro enviado assincronamente, no path especificado."""
  try:
    async with aiofiles.open(save_path, 'wb') as out_file:
      while content := await file.read(1024 * 1024): # Lê em pedaços
        await out_file.write(content)
  except Exception as save_error:
    raise CustomError(500, f"Erro ao guardar o ficheiro: {file.filename}", str(save_error)) from save_error
  finally:
    # Garante que o ficheiro está fechado
    await file.close()

def _prepare_attachment_data(ticket: Tickets, unique_filename: str, original_filename: str, file_ext: str, current_user: dict | None = None) -> dict:
  """Prepara o dicionário para um registo de TicketAttachment."""
  return {
    "filename": unique_filename,
    "original_name": original_filename,
    "extension": file_ext,
    "ticket_id": ticket.id,
    "agent_id": current_user['id'] if current_user else None
  }

async def _bulk_create_attachments(attachment_records_data: list[dict]):
  """Executa um bulk create nos TicketAttachment."""
  if not attachment_records_data:
    return # Não há nada para criar

  try:
    await TicketAttachments.bulk_create([TicketAttachments(**data) for data in attachment_records_data])
  except Exception as db_error:
    raise CustomError(500, "Erro ao guardar anexos na base de dados", str(db_error)) from db_error

def _cleanup_saved_files(saved_file_paths: list[Path]):
  """Tenta remover ficheiros guardados no disco durante uma operação falhada."""
  print(f"Attempting to clean up {len(saved_file_paths)} files due to error...")
  for path in saved_file_paths:
    try:
      if path.is_file():
        os.remove(path)
        print(f"Successfully cleaned up file: {path}")
      else:
        print(f"Skipping cleanup for non-file path: {path}")
    except OSError as cleanup_error:
      print(f"Error cleaning up file {path}: {cleanup_error}")

async def _log_file_addition(ticket: Tickets, attachment_records_data: list[dict], current_user: dict | None = None):
    """Adiciona o log ao adicionar os ficheiros com sucesso."""
    if not attachment_records_data:
      return
    
    if ticket.status_id == 1:
      actor_id = ticket.created_by_id or ticket.requester_id # prioritiza o created_by_id ao requester
    else:
      actor_id = current_user['id']

    await LogService.log_action(
      f"Adicionou {len(attachment_records_data)} anexo(s)",
      actor_id,
      TicketLogs,
      ticket.id,
      None,
      {"attachments_added": attachment_records_data}
    )

# --- Handler de Upload de Ficheiros  ---

async def _handle_file_uploads(ticket: Tickets, files: list[UploadFile], current_user: dict | None = None):
  """
    Lida com a validação, armazenamento, e registo de uploads de ficheiros para um ticket.
    Esta função está implementada para ser chamada dentro de uma transação.
    Se ocorrer algum erro durante a operação, cancela a transação, revertendo todas os passos anteriores.
  """
  if not files:
    return

  attachment_records_data = []
  saved_file_paths = []

  try:
    # Processa e guarda cada ficheiro
    for file in files:
      is_valid, file_ext = _validate_file(file)
      if not is_valid:
        continue # Dá skip de ficheiros inválidos ou lista vazia

      save_path, unique_filename = _generate_save_path(file_ext)

      # Guarda os ficheiros em disco
      await _save_file_to_disk(file, save_path)
      saved_file_paths.append(save_path) # Acompanha os ficheiros guardados para fazer o cleanup em caso de falha

      # Prepara os dados para a DB
      attachment_data = _prepare_attachment_data(ticket, unique_filename, file.filename, file_ext, current_user)
      print("here")
      attachment_records_data.append(attachment_data)

    # Bulk create dos registos de ficheiros
    await _bulk_create_attachments(attachment_records_data)

    # Cria um Log
    await _log_file_addition(ticket, attachment_records_data, current_user)

  except CustomError as e:
    # Tenta fazer um cleanup em qualquer ficheiro inserido durante o processo.
    _cleanup_saved_files(saved_file_paths)
    raise e

  except Exception as e:
    # Tenta fazer um cleanup em qualquer ficheiro inserido durante o processo.
    _cleanup_saved_files(saved_file_paths)
    print(str(e))
    raise CustomError(500, "Erro inesperado no processamento de ficheiros", str(e)) from e


# --- Helpers para update de tickets ---

async def _get_ticket_for_update(uid: str) -> Tickets:
  """Obtem o ticket e preobtem os campos necessários para atualização."""
  ticket = await Tickets.get_or_none(uid=uid).prefetch_related(
    'status', 'priority', 'category', 'subcategory', 'requester',
    'agent', 'company', 'ccs', 'type', 'assistance_type', 'created_by'
  )
  if not ticket:
    raise CustomError(404, "Ticket não encontrado", f"Nenhum ticket encontrado com o UID: {uid}")
  return ticket

def _authorize_ticket_update(ticket: Tickets, current_user: dict):
  """Verifica se o utilizador tem permissão para atualizar o ticket."""
  if not current_user or 'id' not in current_user or 'permissions' not in current_user:
    raise CustomError(401, "Não autenticado", "Informações do utilizador atual inválidas ou ausentes.")

  user_permissions = current_user.get('permissions', [])
  has_tecnico_permission = ('tecnico' in user_permissions)
  # is_agent = (ticket.agent_id == current_user['id']) # Retirar o comentário se o agente deve ser validado

  if not has_tecnico_permission: # and not is_agent: # Adicionar 'and not is_agent' se for necessário validar o agente
    raise CustomError(403, "Acesso negado", "Você não tem permissão para editar este ticket.")

def _prepare_update_data(ticket_data: dict) -> tuple[dict, list[int] | None]:
  """Prepara os dados de atualização, removendo campos protegidos e extraindo as FKs."""
  update_data = ticket_data.dict(exclude_unset=True) # Alterações para campos diretos
  ccs_ids_to_update = update_data.pop('ccs')  # Alterações para fk
  # Se for preciso adicionar fk, é preciso fazer pop e devolver no return para a função mãe 
  # Para poder ser tratado posteriormente

  # Previne alterar campos que não devem ser alterados via update
  protected_fields = ['id', 'uid', 'created_at', 'created_by_id']
  for field in protected_fields:
    update_data.pop(field, None) # Remove o campo se existir

  return update_data, ccs_ids_to_update

def _apply_direct_updates(ticket: Tickets, update_data: dict):
  """Aplica updates nos campos diretos apartir do dict preparado anteriormente "_prepare_update_data"."""
  for key, value in update_data.items():
    if hasattr(ticket, key):
      setattr(ticket, key, value)
    else:
      # Log or handle the warning appropriately
      print(f"Warning: Attempted to update non-existent field '{key}' on ticket {ticket.uid}")

def _handle_automatic_status_update(ticket: Tickets, update_data: dict, original_agent_id_value: int | None):
  """
  Atribui o estado 'In Progress' (ID 2) se um agente for atribuído
  e o ticket não tinha um agente anteriormente.
  """
  agent_id_in_update = 'agent_id' in update_data
  new_agent_id_value = update_data.get('agent_id', None)

  print(original_agent_id_value, update_data['agent_id'])    
  if agent_id_in_update and new_agent_id_value is not None and original_agent_id_value is None:
    # Agente passou de None -> Atribuido altera o estado para "In Progress" (2)
    ticket.status_id = 2
    
  if original_agent_id_value != update_data['agent_id']:
    return True
  return False

def _handle_closed_at_update(ticket: Tickets, old_ticket_details: dict):
  """Atribui ou limpa o timestamp fechado com base no estado."""
  final_status_id = ticket.status_id # Estado depois das alterações diretas e automáticas
  original_status_id = old_ticket_details.get('status_id')

  # Alteração do estado para "Closed" (7)
  if final_status_id == 7 and original_status_id != 7:
    if not ticket.closed_at: # Insere "closed_at" apenas se já não estiver inserido
      ticket.closed_at = datetime.now()
  # Alteração de estado de "Closed" (7) para "Reopen" (8)
  elif final_status_id != 7 and original_status_id == 7:
    ticket.closed_at = None # Limpa o "closed_at"

async def _handle_ccs_update(ticket: Tickets, ccs_ids_to_update: list[int] | None):
  """Atualiza a lista de CCS para o ticket."""
  if ccs_ids_to_update is not None: # Permite lista vazia para limpar os ccs
    await ticket.ccs.clear() # Remove relações existentes de CCS
    if ccs_ids_to_update: # Se a lista não estiver vazia, obtem e adiciona novos
      ccs_employees = await get_users_by_ids(ccs_ids_to_update)
      if ccs_employees:
        await ticket.ccs.add(*ccs_employees)

async def _handle_update_logging(ticket: Tickets, old_ticket_details: dict, ccs_ids_to_update: list[int] | None, current_user_id: int):
    """Regista as alterações feitas no ticket."""
    new_ticket_details = await ticket.to_dict_log()

    # Filter details to only include changed fields for the log description
    changed_details = {
      k: new_ticket_details[k]
      for k in new_ticket_details
      if k not in old_ticket_details or new_ticket_details[k] != old_ticket_details[k]
    }
    
    old_details = {
      k: old_ticket_details[k]
      for k in new_ticket_details
      if k not in old_ticket_details or new_ticket_details[k] != old_ticket_details[k]
    }
    
    # Add CCS update info to the log if it was part of the request
    if ccs_ids_to_update is not None:
      old_details['ccs'] = f"Alterado dos ids: {old_ticket_details['ccs']}"
      changed_details['ccs'] = f"Atualizado para os ids: {ccs_ids_to_update}" # Or fetch names if needed

    # Only log if there were actual changes detected
    if changed_details:
      await LogService.log_action(
        "Atualizado",
        current_user_id,
        TicketLogs,
        ticket.id,
        old_details,
        changed_details
      )
    # return changed_details # Return changed_details for potential use in notifications

async def _handle_update_notifications(ticket: Tickets, assigned: bool = False):
  """Envia notificações, via email se o estado for alterado para fechado, reaberto ou se o agente for alterado."""
  
  if assigned:
    print("Assigned")
    try:
      # Se um agente foi alocado envia email
      final_details = await ticket.to_dict_details()
      await _handle_ticket_emails(ticket, final_details, "assigned")
    except Exception as email_error:
      print(f"Failed to send assigned email for ticket UID {ticket.uid}: {email_error}")
  elif ticket.status_id == 7:
    print("Closed")
    try:
      # Se o estado foi alterado para 7 (Fechado) enviar email
      final_details = await ticket.to_dict_details()
      await _handle_ticket_emails(ticket, final_details, "closed")
    except Exception as email_error:
      print(f"Failed to send status change email for ticket UID {ticket.uid}: {email_error}")
  elif ticket.status_id == 8:
    print("Reopened")
    try:
      # Se o estado for alterado para 8 (Reaberto) enviar email
      final_details = await ticket.to_dict_details()
      await _handle_ticket_emails(ticket, final_details, "reopened")
    except Exception as email_error:
      print(f"Failed to send status change email for ticket UID {ticket.uid}: {email_error}")

async def _handle_ticket_emails(ticket: Tickets, ticket_info: dict, email_type: str | None = None):
  """
    Lida com o envio de emails relacionados com o ticket.

    Args:
      ticket: O objeto do ticket.
      ticket_info: Um dicionário que contém detalhes do ticket.
      email_type: O tipo de email que será enviado ("assigned", "closed", "reopened").
  """
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