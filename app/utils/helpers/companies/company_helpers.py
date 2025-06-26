from app.database.models.helpdesk import (
  Companies, Locals, TicketCategories_Companies, TicketCategories
)
from app.utils.errors.exceptions import CustomError
from tortoise.exceptions import DoesNotExist
import logging

logger = logging.getLogger(__name__)

def _validate_company_creation_data(company_data: dict):
  """Valida os dados de entrada para a criação da empresa e seus locais."""
  required_fields = ["name", "acronym"]
  for field in required_fields:
    if field not in company_data or not company_data[field]:
      raise CustomError(400, f"Campo obrigatório '{field}' ausente ou vazio para a empresa.")

  locals_to_create_data = company_data.get("locals", [])
  if not isinstance(locals_to_create_data, list):
    raise CustomError(400, "O campo 'locals' deve ser uma lista.")
      
  for i, local_data in enumerate(locals_to_create_data):
    if not isinstance(local_data, dict):
      raise CustomError(400, f"Cada item em 'locals' deve ser um dicionário. Item {i} inválido.")
    required_local_fields = ["name", "short"]
    for f in required_local_fields:
      if f not in local_data or not local_data[f]:
        raise CustomError(400, f"Campo obrigatório '{f}' ausente ou vazio para o local {i+1}.")

async def _create_locals_for_company(company: Companies, locals_data: list[dict]):
  """Cria e associa locais a uma empresa."""
  for local_data in locals_data:
    await Locals.create(company=company, **local_data)

async def _associate_ticket_categories_with_company(company: Companies, category_ids: list[int]):
  """Associa categorias de ticket a uma empresa."""
  for category_id in category_ids:
    try:
      ticket_category = await TicketCategories.get(id=category_id)
      await TicketCategories_Companies.create(
        company=company,
        ticket_category=ticket_category
      )
    except DoesNotExist:
      logger.warning(f"TicketCategory com ID {category_id} não encontrado ao tentar associar com a empresa {company.name}. Pulando associação.")
      # Consider raising CustomError(404, ...) if this should be a hard failure.

async def _manage_locals_for_update(company: Companies, locals_update_data: list[dict]):
  """
  Gerencia a criação, atualização e exclusão de locais para uma empresa.
  """
  current_locals_orm = await Locals.filter(company=company).all()
  current_locals_map = {local_orm.id: local_orm for local_orm in current_locals_orm}
  
  processed_local_ids = set()

  for local_data in locals_update_data:
    if not isinstance(local_data, dict):
        raise CustomError(400, "Cada item em 'locals' deve ser um dicionário.")

    local_id = local_data.get("id")

    if local_id:  # Local existente: atualizar
      processed_local_ids.add(local_id)
      local_to_update = current_locals_map.get(local_id)
      if not local_to_update:
        logger.warning(f"Local com ID {local_id} fornecido para atualização não encontrado para a empresa {company.id}. Pulando.")
        continue
      
      update_fields = []
      for field_key in ["name", "short"]:
        if field_key in local_data:
          field_value = local_data[field_key]
          if not field_value: # Garantir que campos não sejam vazios se fornecidos
              raise CustomError(400, f"Campo '{field_key}' do local ID {local_id} não pode ser vazio se fornecido para atualização.")
          setattr(local_to_update, field_key, field_value)
          update_fields.append(field_key)
      if update_fields:
        await local_to_update.save(update_fields=update_fields)
    
    else:  # Novo local: criar
      required_new_local_fields = ["name", "short"]
      for f_new in required_new_local_fields:
        if f_new not in local_data or not local_data[f_new]:
          raise CustomError(400, f"Campo obrigatório '{f_new}' ausente ou vazio para um novo local.")
      
      # Coleta apenas os campos permitidos para criação
      new_local_payload = {k: v for k, v in local_data.items() if k in required_new_local_fields}
      new_local = await Locals.create(company=company, **new_local_payload)
      # Não é necessário adicionar new_local.id a processed_local_ids para a lógica de exclusão atual

  # Excluir locais que existiam mas não estão na lista de processados (ou seja, foram omitidos da entrada)
  for local_id_to_check, local_orm_to_check in current_locals_map.items():
    if local_id_to_check not in processed_local_ids:
      await local_orm_to_check.delete()

async def _manage_ticket_categories_for_update(company: Companies, new_ticket_category_ids: list[int]):
  """
  Gerencia as associações de categorias de ticket para uma empresa.
  """
  if not all(isinstance(cat_id, int) for cat_id in new_ticket_category_ids):
    raise CustomError(400, "Todos os IDs em 'ticket_category_ids' devem ser números inteiros.")

  current_associations = await TicketCategories_Companies.filter(company=company).all()
  current_linked_category_ids = {assoc.ticket_category_id for assoc in current_associations}
  
  target_ids_set = set(new_ticket_category_ids)

  # Categorias para adicionar
  ids_to_add_link_for = target_ids_set - current_linked_category_ids
  for cat_id_to_add in ids_to_add_link_for:
    try:
      ticket_category = await TicketCategories.get(id=cat_id_to_add)
      await TicketCategories_Companies.create(company=company, ticket_category=ticket_category)
    except DoesNotExist:
      logger.warning(f"TicketCategory com ID {cat_id_to_add} não encontrado ao tentar associar com a empresa {company.name}. Pulando associação.")
      # Considere levantar CustomError(404, ...) se esta deve ser uma falha crítica.

  # Associações para remover
  ids_to_remove_links_for = current_linked_category_ids - target_ids_set
  if ids_to_remove_links_for:
    await TicketCategories_Companies.filter(
      company=company, 
      ticket_category_id__in=list(ids_to_remove_links_for)
    ).delete()