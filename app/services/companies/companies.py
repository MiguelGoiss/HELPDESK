from datetime import datetime, timezone
import logging
from app.database.models.helpdesk import (
  Companies, Locals, TicketCategories, TicketCategories_Companies
)

from app.utils.errors.exceptions import CustomError
from tortoise.transactions import in_transaction
from tortoise.exceptions import IntegrityError, DoesNotExist
from app.utils.helpers.companies.company_helpers import (
  _validate_company_creation_data,
  _create_locals_for_company,
  _associate_ticket_categories_with_company,
  _manage_locals_for_update,
  _manage_ticket_categories_for_update,
)

logger = logging.getLogger(__name__)

async def create_company(company_data: dict) -> Companies:
  """
  Cria uma nova empresa com locais e associações de categorias de ticket.

  Args:
    company_data: Um dicionário que contém os dados da empresa.
      Exemplo esperado:
      {
        "name": "Nome da Empresa",
        "acronym": "ACRO",
        "locals": [
          {"name": "Local 1", "short": "L1", "background": "#FFFFFF", "text": "#000000"},
          {"name": "Local 2", "short": "L2", "background": "#0000FF", "text": "#FFFFFF"}
        ],
        "ticket_category_ids": [1, 2] # ids de TicketCategories existentes
      }

  Returns:
    O objeto Companies ORM criado.

  Raises:
    CustomError: Se ocorrer algum erro durante a criação, como dados inválidos,
                 conflitos de integridade (ex: nome da empresa duplicado) ou
                 categorias de ticket não encontradas.
    ValueError: Se campos obrigatórios estiverem faltando (será encapsulado em CustomError).
  """
  company_dict = company_data.dict()
  _validate_company_creation_data(company_dict)
  company_name = company_dict["name"]
  company_acronym = company_dict["acronym"]
  locals_to_create_data = company_dict.get("locals", [])
  category_ids_to_link = company_dict.get("ticket_category_ids", [])

  try:
    async with in_transaction('helpdesk'):
      # 1. Cria a empresa
      new_company = await Companies.create(
        name=company_dict["name"],
        acronym=company_dict["acronym"]
      )

      # 2. Cria e associa os locais
      if locals_to_create_data:
        await _create_locals_for_company(new_company, locals_to_create_data)

      # 3. Cria associações com categorias de ticket
      if category_ids_to_link:
        await _associate_ticket_categories_with_company(new_company, category_ids_to_link)
      
      return new_company

  except IntegrityError as e:
    logger.error(f"Integrity error creating company '{company_name}': {e}", exc_info=True)
    if "companies_name_key" in str(e).lower() or "unique constraint failed: companies.name" in str(e).lower(): # Adapt based on DB
      raise CustomError(409, f"Empresa com nome '{company_name}' já existe.") from e

    raise CustomError(409, "Erro de integridade ao criar empresa. Verifique se há dados duplicados (ex: nome, ou associação de categoria).") from e

  except Exception as e:
    logger.error(f"Unexpected error creating company '{company_name}': {e}", exc_info=True)
    raise CustomError(500, "Ocorreu um erro inesperado ao criar a empresa.") from e

async def fetch_companies() -> list[dict]:
  """
  Obtém todas as empresas ativas, incluindo seus locais.

  Returns:
    Uma lista de dicionários, onde cada dicionário representa uma empresa com seus locais.

  Raises:
    CustomError: Se ocorrer algum erro durante a busca dos dados.
  """
  try:
    # Filtra empresas que não estão desativadas (deactivated_at é Nulo) e ordena pelo nome.
    # Prefetch related locals to avoid N+1 queries.
    companies_orm = await Companies.filter(
      deactivated_at__isnull=True
    ).prefetch_related('company_local_relations').order_by('name').all()

    return [await company.to_dict_related() for company in companies_orm]

  except Exception as e:
    logger.error(f"Unexpected error fetching companies: {e}", exc_info=True)
    raise CustomError(
      500,
      "Ocorreu um erro ao obter as empresas.",
      str(e)
    ) from e
    
async def fetch_company_by_id(company_id: int) -> Companies:
  """
  Obtém uma empresa específica pelo seu ID, incluindo seus locais e categorias de ticket associadas.

  Args:
    company_id: O ID da empresa a ser buscada.

  Returns:
    O objeto Companies ORM com os locais e categorias de ticket relacionados pré-carregados.

  Raises:
    CustomError: Se a empresa não for encontrada (404) ou se ocorrer outro erro (500).
  """
  try:
    company_orm = await Companies.filter(id=company_id).prefetch_related(
      'company_local_relations', 
      'company_ticket_categories'
    ).get()
    
    return await company_orm.to_dict_details()

  except DoesNotExist:
    logger.warning(f"Company with ID {company_id} not found.")
    raise CustomError(
      404,
      f"Empresa com ID {company_id} não encontrada."
    ) from None

  except Exception as e:
    logger.error(f"Unexpected error fetching company with ID {company_id}: {e}", exc_info=True)
    raise CustomError(
      500,
      "Ocorreu um erro ao obter a empresa.",
      str(e)
    ) from e

async def update_company_details(company_id: int, company_data: dict) -> Companies:
  """
  Atualiza os detalhes de uma empresa, incluindo seus locais e associações de categorias de ticket.

  Args:
    company_id: O ID da empresa a ser atualizada.
    company_data: Um dicionário contendo os dados da empresa para atualização.
                  Campos como 'name', 'acronym' são atualizados diretamente.
                  'locals': uma lista de dicionários de locais. Locais com 'id' são atualizados,
                            sem 'id' são criados. Locais existentes não na lista são removidos.
                  'ticket_category_ids': uma lista de IDs de categorias de ticket. As associações
                                         são sincronizadas com esta lista.

  Returns:
    O objeto Companies ORM atualizado com relações pré-carregadas.

  Raises:
    CustomError: Se a empresa não for encontrada (404), dados inválidos (400),
                 conflito de integridade (409), ou outro erro (500).
  """
  try:
    company_data_dict = company_data.dict(exclude_unset=True) 
    async with in_transaction('helpdesk'):
      company_to_update = await Companies.get(id=company_id)

      update_fields_company = []
      if "name" in company_data_dict:
        if not company_data_dict["name"]:
          raise CustomError(400, "O nome da empresa não pode ser vazio se fornecido para atualização.")
        company_to_update.name = company_data_dict["name"]
        update_fields_company.append("name")
      if "acronym" in company_data_dict:
        if not company_data_dict["acronym"]:
          raise CustomError(400, "O acrônimo da empresa não pode ser vazio se fornecido para atualização.")
        company_to_update.acronym = company_data_dict["acronym"]
      
      if update_fields_company:
        await company_to_update.save(update_fields=update_fields_company)

      if "locals" in company_data_dict:
        await _manage_locals_for_update(company_to_update, company_data_dict.get("locals", []))

      if "ticket_category_ids" in company_data_dict:
        await _manage_ticket_categories_for_update(company_to_update, company_data_dict.get("ticket_category_ids", []))

      # Refetch para garantir que todas as relações estejam populadas e atualizadas no objeto devolvido
      updated_company = await Companies.filter(id=company_id).prefetch_related(
        'company_local_relations', 
        'company_ticket_categories'
      ).get()
      return updated_company

  except DoesNotExist:
    logger.warning(f"Empresa com ID {company_id} não encontrada para atualização.")
    raise CustomError(404, f"Empresa com ID {company_id} não encontrada.") from None
  
  except IntegrityError as e:
    logger.error(f"Erro de integridade ao atualizar empresa {company_id}: {e}", exc_info=True)
    company_name_for_error = company_data.get('name', company_to_update.name if 'company_to_update' in locals() else 'desconhecido')
    if "companies_name_key" in str(e).lower() or "unique constraint failed: companies.name" in str(e).lower():
         raise CustomError(409, f"Já existe uma empresa com o nome '{company_name_for_error}'.") from e
    raise CustomError(409, "Erro de integridade ao atualizar empresa. Verifique dados duplicados.") from e
  
  except CustomError: # Re-levanta CustomErrors de validações ou helpers
    raise

  except Exception as e:
    logger.error(f"Erro inesperado ao atualizar empresa {company_id}: {e}", exc_info=True)
    raise CustomError(500, "Ocorreu um erro inesperado ao atualizar a empresa.") from e
  
async def deactivate_company(company_id: int) -> None:
  """
  Desativa uma empresa definindo o campo 'deactivated_at'.

  Args:
    company_id: O ID da empresa a ser desativada.

  Raises:
    CustomError: Se a empresa não for encontrada (404) ou se ocorrer outro erro (500).
  """
  try:
    company = await Companies.get(id=company_id)
    if company.deactivated_at is not None:
      logger.info(f"Empresa com ID {company_id} já está desativada.")
      return

    company.deactivated_at = datetime.now(timezone.utc)
    await company.save(update_fields=['deactivated_at'])
    logger.info(f"Empresa com ID {company_id} desativada com sucesso.")

  except DoesNotExist:
    logger.warning(f"Empresa com ID {company_id} não encontrada para desativação.")
    raise CustomError(
      404,
      f"Empresa com ID {company_id} não encontrada."
    ) from None

  except Exception as e:
    logger.error(f"Erro inesperado ao desativar empresa com ID {company_id}: {e}", exc_info=True)
    raise CustomError(
      500,
      "Ocorreu um erro inesperado ao desativar a empresa.",
      str(e)
    ) from e
