from tortoise.expressions import Q
from app.database.models.helpdesk import Tickets, TicketLogs, TicketPresets
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
  _apply_filters,
)
from app.utils.errors.exceptions import CustomError
from app.utils.helpers.paginate import paginate
from datetime import datetime
from app.services.logs import LogService
from tortoise.functions import Count
from tortoise.transactions import in_transaction
from fastapi import UploadFile
import json
import time
import logging

logger = logging.getLogger(__name__)

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
      logger.error(f"Error during transaction, rollback initiated: {e}", exc_info=True)
      raise CustomError(500, "Ocorreu um erro durante a criação do ticket ou processamento de anexos", str(e)) from e

  # Envia o email de confirmação para o cliente com técnico (se houver) e os utilizadores selecionados como ccs em cc
  try:
    await _handle_ticket_emails(new_ticket_orm, updated_ticket_details, "create")
  except Exception as email_error:
    logger.error(f"Error sending ticket creation email for ticket {new_ticket_orm.id if new_ticket_orm else 'N/A'}: {email_error}", exc_info=True)
    raise CustomError(
      500,
      "Ocorreu um erro a enviar o email",
      str(email_error)
    )

  updated_ticket_details.pop("uid")
  return updated_ticket_details

# --- Fim da criação do ticket ---

# --- Inicio do get de todos os tickets ---

async def fetch_tickets(
  path: str,
  page_size: int,
  page: int,
  current_user: dict,
  own: bool | None,
  original_query_params: dict | None,
  # O parametro search serve para pesquisa geral (OR)
  search: str | None,
  # Dict para pesquisa especifica (AND)
  and_filters: dict[str, any] | None,
  # Campos para ordenação, usar o prefixo '-' para descendente
  order_by: str | None
  ) -> dict:
  start = time.time()
  queryset = Tickets.all()

  # Aplica os filtros
  queryset = _apply_filters(queryset, and_filters, search, order_by)
  # Filtros para o search (AND)
  # if and_filters:
  #   queryset = await _apply_and_filters(queryset, and_filters)

  # # Aplica search geral (OR)
  # queryset = _apply_or_search(queryset, search)

  # # Aplica o order
  # queryset = _apply_ordering(queryset, order_by)

  # Annotate com count para obter a contagem dos attachments em vez dos attachments
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
    logger.error(f"Error during ticket pagination: {e}", exc_info=True)
    raise CustomError(500, "Erro ao processar a lista de tickets.", str(e)) from e

  end = time.time()
  logger.info(f"fetch_tickets execution time: {end-start:.4f}s")
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
      logger.warning(f"Ticket not found with UID: {uid}")
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
      logger.error(f"Error during ticket update transaction for UID {uid}, rollback initiated: {e}", exc_info=True)
      raise CustomError(500, "Ocorreu um erro ao atualizar o ticket", str(e)) from e
  
  # ---  Notifica o requerente ---
  # Envia email após todas as alterações.
  try:
    await _handle_update_notifications(ticket, assigned)
  except Exception as email_error:
    logger.error(f"Error sending update notification for ticket UID {uid}: {email_error}", exc_info=True)

  try:
    updated_ticket_details = await fetch_ticket_details(uid)
    return updated_ticket_details

  except CustomError as e:
    raise e
  
  except Exception as e:
    raise CustomError(500, "Erro ao obter detalhes atualizados do ticket após a atualização.", str(e)) from e

# --- Fim da atualização de um ticket ---

# --- Inicio dos counts dos presets ---

async def fetch_preset_counts(search: str | None , and_filters: dict[str, any] | None, own: bool | None, current_user: dict | None) -> list[dict]:
  """
  Calcula a contagem de tickets para cada preset definido,
  opcionalmente aplicando filtros base adicionais.

  Args:
    and_filters: Um dicionário opcional de filtros a serem aplicados
                 antes dos filtros específicos de cada preset.

  Returns:
    Uma lista de dicionários, cada um contendo 'name' (nome do preset)
    e 'count' (contagem de tickets correspondente).

  Raises:
    CustomError: Se houver um erro ao aplicar os filtros base.
  """
  presets = await TicketPresets.filter(main=True).all()
  results = []

  # Cria um queryset base
  base_queryset = Tickets.all()
  
  if own:
    base_queryset = base_queryset.filter(Q(requester_id=current_user['id']) | Q(agent_id=current_user['id']))

  for preset in presets:
    preset_queryset = base_queryset # Começa com o queryset base (já filtrado se and_filters foi passado)
    if preset.filter:
      try:
        preset_filter_dict = json.loads(preset.filter)
          
        if isinstance(preset_filter_dict, dict):
          # Aplica os filtros específicos do preset sobre o queryset base
          preset_queryset = _apply_filters(preset_queryset, preset_filter_dict)
        else:
          logger.warning(f"Preset '{preset.name}' (ID: {preset.id}) filter is not a valid JSON object. Skipping preset filters.")
      except json.JSONDecodeError:
        logger.warning(f"Warning: Could not parse filter for preset '{preset.name}' (ID: {preset.id}). Skipping preset filters.")
      except CustomError as e:
        # Erro ao aplicar filtros do *preset* (e.g., campo inválido no preset)
        logger.warning(f"Warning: Invalid filter found in preset '{preset.name}' (ID: {preset.id}): {e}. Skipping preset filters.")
      except Exception as e:
        logger.warning(f"Unexpected error applying filter for preset '{preset.name}' (ID: {preset.id}): {e}. Skipping preset filters.", exc_info=True)
    # Conta os tickets após aplicar os filtros do preset (ou apenas os filtros base se o preset não tiver filtro ou for inválido)
    try:
      count = await preset_queryset.count()
      results.append({"id": preset.id, "name": preset.name, "filter":preset.filter, "color":preset.color, "count": count})
    except Exception as e:
      # Log error during the count operation for a specific preset
      logger.error(f"Error counting tickets for preset '{preset.name}' (ID: {preset.id}): {e}", exc_info=True)
      # Append a result indicating an error or skip this preset
      results.append({"id": preset.id, "name": preset.name, "filter":json.loads(preset.filter), "color":preset.color, "count": "Error"}) # Or handle as needed

  return results

# --- Fim dos counts dos presets ---

    
