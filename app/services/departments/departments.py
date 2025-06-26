import logging
from app.database.models.helpdesk import (
  Departments, Companies, Employees
)
from app.utils.errors.exceptions import CustomError
from tortoise.transactions import in_transaction
from tortoise.exceptions import IntegrityError, DoesNotExist
from datetime import datetime, timezone
from ...utils.helpers.filtering import (
  _apply_and_filters,
  _apply_or_search,
  _apply_ordering, 
)
from app.utils.helpers.paginate import paginate
import time

logger = logging.getLogger(__name__)

# It's good practice to use Pydantic schemas for request data validation.
# For this example, we'll assume department_data is a dict.
# If you have a Pydantic schema, e.g., DepartmentCreateSchema,
# you would change the type hint: department_data: DepartmentCreateSchema

async def create_department(department_data: dict) -> Departments:
  """
  Cria um novo departamento e opcionalmente o associa a empresas.

  Args:
    department_data: Um dicionário contendo os dados do departamento.
      Exemplo esperado:
      {
        "name": "Nome do Departamento", // Obrigatório
        "company_ids": [1, 2] // Opcional: Lista de IDs de empresas existentes
      }

  Returns:
    O departamento criado.

  Raises:
    CustomError: Se ocorrer algum erro durante a criação, como dados inválidos,
                 conflitos de integridade (ex: nome do departamento duplicado),
                 ou empresas não encontradas.
  """
  department_data = department_data.dict()
  department_name = department_data.get("name")
  if not department_name:
    raise CustomError(400, "O nome do departamento é obrigatório.")

  company_ids_to_link = department_data.get("company_ids", [])
  if not isinstance(company_ids_to_link, list):
    raise CustomError(400, "O campo 'company_ids' deve ser uma lista de IDs.")

  companies_to_link = []
  if company_ids_to_link:
    # Fetch all companies to link in a single query
    companies_to_link = await Companies.filter(id__in=company_ids_to_link).all()
    
    # Check if all provided company IDs were found
    if len(companies_to_link) != len(company_ids_to_link):
      found_ids = {c.id for c in companies_to_link}
      not_found_ids = list(set(company_ids_to_link) - found_ids)
      raise CustomError(404, f"Empresas com IDs {not_found_ids} não encontradas.")
  try:
    async with in_transaction('helpdesk'):
      # 1. Cria o departamento
      new_department = await Departments.create(name=department_name)

      # 2. Associa o departamento a empresas, se fornecido
      # for company_id in company_ids_to_link:
      #   # We already fetched and validated companies_to_link before the transaction
      await new_department.companies.add(*companies_to_link)

      return new_department

  except IntegrityError as e:
    logger.error(f"Erro de integridade ao criar departamento '{department_name}': {e}", exc_info=True)
    if "departments_name_key" in str(e).lower() or "unique constraint failed: departments.name" in str(e).lower():
      raise CustomError(409, f"Departamento com nome '{department_name}' já existe.") from e
    raise CustomError(409, "Erro de integridade ao criar departamento. Verifique dados duplicados.") from e

  except Exception as e:
    logger.error(f"Erro inesperado ao criar departamento '{department_name}': {e}", exc_info=True)
    raise CustomError(500, "Ocorreu um erro inesperado ao criar o departamento.") from e
  
async def fetch_departments() -> list[dict]:
  """
  Obtém todos os departamentos, incluindo as empresas associadas a cada um.

  Returns:
    Uma lista de dicionários, onde cada dicionário representa um departamento
    com uma lista de suas empresas associadas.

  Raises:
    CustomError: Se ocorrer algum erro durante a busca dos dados.
  """
  try:
    departments_orm = await Departments.all().prefetch_related('companies')
    
    # Utiliza o método de serialização do modelo Department que inclui as empresas.
    return [department.to_dict_with_companies() for department in departments_orm]

  except Exception as e:
    logger.error(f"Erro inesperado ao buscar departamentos: {e}", exc_info=True)
    raise CustomError(500, "Ocorreu um erro ao obter os departamentos.") from e

#--- ALLOWED FIELDS FOR FILTERING AND ORDER ---#
ALLOWED_AND_FILTER_FIELDS: set[str] = {
  "id",
  "name"
}

DEFAULT_OR_SEARCH_FIELDS: set[str] = [
  "id",
  "name"
]

ALLOWED_ORDER_FIELDS: set[str] = {
  "id",
  "name"
}

async def fetch_departments_management(
    path: str,
    page_size: int,
    page: int,
    original_query_params: dict | None,
    # O parametro search serve para pesquisa geral (OR)
    search: str | None,
    # Dict para pesquisa especifica (AND)
    and_filters: dict[str, any] | None,
    # Campos para ordenação, usar o prefixo '-' para descendente
    order_by: str | None
  ):
  start = time.time()
  
  queryset = Departments.all()
  
  if and_filters:
    queryset = _apply_and_filters(queryset, None, ALLOWED_AND_FILTER_FIELDS, and_filters)
  
  if search:
    queryset = _apply_or_search(queryset, DEFAULT_OR_SEARCH_FIELDS, search)

  queryset = _apply_ordering(queryset, ALLOWED_ORDER_FIELDS, "-id", order_by)

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
    logger.error(f"Error during departments pagination: {e}", exc_info=True)
    raise CustomError(500, "Erro ao processar a lista de departamentos.", str(e)) from e

  end = time.time()
  logger.info(f"fetch_tickets execution time: {end-start:.4f}s")
  return paginated_result

async def fetch_department_by_id(department_id: int) -> Departments:
  """
  Obtém um departamento específico pelo seu ID, incluindo as empresas associadas.

  Args:
    department_id: O ID do departamento a ser buscado.

  Returns:
    O objeto Departments ORM com as empresas relacionadas pré-carregadas.

  Raises:
    CustomError: Se o departamento não for encontrado (404) ou se ocorrer outro erro (500).
  """
  try:
    # Busca o departamento e pré-carrega a relação 'companies'
    department_orm = await Departments.filter(id=department_id).prefetch_related('companies').get()
    return department_orm.to_dict_with_companies()
  
  except DoesNotExist:
    logger.warning(f"Departamento com ID {department_id} não encontrado.")
    raise CustomError(
      404,
      f"Departamento com ID {department_id} não encontrado."
    ) from None
    
  except Exception as e:
    logger.error(f"Erro inesperado ao buscar departamento com ID {department_id}: {e}", exc_info=True)
    raise CustomError(
      500,
      "Ocorreu um erro ao obter o departamento."
    ) from e

async def _manage_companies_for_department_update(department: Departments, new_company_ids: list[int]):
  """
  Gerencia as associações de empresas para um departamento.
  Sincroniza as associações existentes com a lista de IDs fornecida.
  """
  if not all(isinstance(comp_id, int) for comp_id in new_company_ids):
    raise CustomError(400, "Todos os IDs em 'company_ids' devem ser números inteiros.")

  # Get current associations
  current_companies = await department.companies.all()
  current_linked_company_ids = {c.id for c in current_companies}

  target_ids_set = set(new_company_ids)

  # Companies to add
  ids_to_add_link_for = target_ids_set - current_linked_company_ids
  companies_to_add = []
  if ids_to_add_link_for:
    # Fetch companies to add in a single query
    companies_to_add = await Companies.filter(id__in=list(ids_to_add_link_for)).all()
    # Check if all provided IDs were found
    if len(companies_to_add) != len(ids_to_add_link_for):
      found_ids = {c.id for c in companies_to_add}
      not_found_ids = list(ids_to_add_link_for - found_ids)
      raise CustomError(404, f"Empresas com IDs {not_found_ids} não encontradas para associação.")

  # Companies to remove
  ids_to_remove_links_for = current_linked_company_ids - target_ids_set
  companies_to_remove = [c for c in current_companies if c.id in ids_to_remove_links_for] # Use the already fetched current_companies

  # Perform updates (this helper is called inside the main transaction)
  if companies_to_add:
    await department.companies.add(*companies_to_add)
  if companies_to_remove:
    await department.companies.remove(*companies_to_remove)

async def update_department_details(department_id: int, department_data: dict) -> Departments:
  """
  Atualiza os detalhes de um departamento, incluindo suas associações com empresas.

  Args:
    department_id: O ID do departamento a ser atualizado.
    department_data: Um dicionário contendo os dados do departamento para atualização.
      Exemplo esperado:
      {
        "name": "Novo Nome do Departamento", // Opcional
        "company_ids": [1, 3] // Opcional: Lista de IDs de empresas para associar.
                              // As associações serão sincronizadas com esta lista.
      }

  Returns:
    O objeto Departments ORM atualizado com as empresas relacionadas pré-carregadas.

  Raises:
    CustomError: Se o departamento não for encontrado (404), dados inválidos (400),
                 conflito de integridade (409), ou outro erro (500).
  """
  try:
    department_data_dict = department_data.dict(exclude_unset=True) # If using Pydantic
    # department_data_dict = {k: v for k, v in department_data.items() if v is not None}

    async with in_transaction('helpdesk'):
      department_to_update = await Departments.filter(id=department_id).first()
      if not department_to_update:
        raise DoesNotExist(f"Departamento com ID {department_id} não encontrado.")

      if "name" in department_data_dict:
        new_name = department_data_dict["name"]
        if not new_name:
          raise CustomError(400, "O nome do departamento não pode ser vazio se fornecido para atualização.")
        department_to_update.name = new_name
        await department_to_update.save(update_fields=["name"])

      if "company_ids" in department_data_dict:
        company_ids_to_set = department_data_dict.get("company_ids", [])
        if not isinstance(company_ids_to_set, list):
            raise CustomError(400, "O campo 'company_ids' deve ser uma lista.")
        await _manage_companies_for_department_update(department_to_update, company_ids_to_set)

      # Refetch para garantir que todas as relações estejam populadas e atualizadas no objeto devolvido
      updated_department = await Departments.filter(id=department_id).prefetch_related('companies').get()
      return updated_department.to_dict_with_companies()

  except DoesNotExist:
    logger.warning(f"Departamento com ID {department_id} não encontrado para atualização.")
    raise CustomError(404, f"Departamento com ID {department_id} não encontrado.") from None
  
  except IntegrityError as e:
    logger.error(f"Erro de integridade ao atualizar departamento {department_id}: {e}", exc_info=True)
    department_name_for_error = department_data_dict.get('name', department_to_update.name if 'department_to_update' in locals() else 'desconhecido')
    if "departments_name_key" in str(e).lower() or "unique constraint failed: departments.name" in str(e).lower():
         raise CustomError(409, f"Já existe um departamento com o nome '{department_name_for_error}'.") from e
    raise CustomError(409, "Erro de integridade ao atualizar departamento. Verifique dados duplicados.") from e
  
  except CustomError:
    raise

  except Exception as e:
    logger.error(f"Erro inesperado ao atualizar departamento {department_id}: {e}", exc_info=True)
    raise CustomError(500, "Ocorreu um erro inesperado ao atualizar o departamento.") from e

async def deactivate_department(department_id: int) -> None:
  """
  Desativa um departamento definindo o campo 'deactivated_at'.
  Verifica se o departamento tem colaboradores associados antes de desativar.

  Args:
    department_id: O ID do departamento a ser desativado.

  Raises:
    CustomError: Se o departamento não for encontrado (404),
                 se o departamento tiver colaboradores associados (409 - conflito),
                 ou se ocorrer outro erro (500).
  """
  try:
    async with in_transaction('helpdesk'):
      department_to_deactivate = await Departments.filter(id=department_id).prefetch_related('department_relations').get() # department_relations is the related_name from Employees

      if department_to_deactivate.deactivated_at is not None:
        logger.info(f"Departamento com ID {department_id} já está desativado.")
        return

      active_employees_count = await department_to_deactivate.department_relations.filter(
        deactivated_at__isnull=True,
        deleted_at__isnull=True
      ).count()

      if active_employees_count > 0:
        logger.warning(f"Tentativa de desativar o departamento {department_id} que possui {active_employees_count} colaborador(es) ativo(s) associado(s).")
        raise CustomError(
          409,
          f"Não é possível desativar o departamento '{department_to_deactivate.name}' pois ele possui {active_employees_count} colaborador(es) ativo(s) associado(s)."
        )

      department_to_deactivate.deactivated_at = datetime.now(timezone.utc)
      await department_to_deactivate.save(update_fields=['deactivated_at'])
      logger.info(f"Departamento com ID {department_id} ('{department_to_deactivate.name}') desativado com sucesso.")

  except DoesNotExist:
    logger.warning(f"Departamento com ID {department_id} não encontrado para desativação.")
    raise CustomError(
      404,
      f"Departamento com ID {department_id} não encontrado."
    ) from None
  
  except CustomError:
    raise

  except Exception as e:
    logger.error(f"Erro inesperado ao desativar departamento com ID {department_id}: {e}", exc_info=True)
    raise CustomError(
      500,
      "Ocorreu um erro inesperado ao desativar o departamento."
    ) from e