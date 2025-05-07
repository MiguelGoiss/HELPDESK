import logging
from functools import reduce # For OR search
from operator import or_ # For OR search

from app.database.models.helpdesk import (
    TicketCategories,
    TicketSubcategories, # Used by TicketCategories.to_dict
    Companies            # Used by TicketCategories.to_dict and for filtering
)
from app.utils.errors.exceptions import CustomError
from app.utils.helpers.tickets.categories.ticket_categories import _validate_category_name
from app.utils.helpers.paginate import paginate # Assuming this is the correct path to your paginate helper
from tortoise.expressions import Q # For OR search

logger = logging.getLogger(__name__)

async def create_ticket_category(category_data: dict) -> TicketCategories:
  """
  Cria uma nova categoria de tickets.

  Args:
    category_data (dict): Um dicionário que contém os dados da nova categoria.
                          Parâmetros esperados: 'name', 'description' (Opcional),
                          'companies' (Opcional: lista de ids de empresas).

  Returns:
    Um dicionário com os dados da nova categoria.

  Raises:
    CustomError: Se uma categoria com o mesmo nome já existir
                 ou se ocorrerem erros na base de dados.
  """
  try:
    category_name = category_data.get('name')
    await _validate_category_name(category_name)

    company_ids = category_data.pop('companies', None)
    
    new_category = await TicketCategories.create(**category_data)

    if company_ids:
      companies_to_add = await Companies.filter(id__in=company_ids, active=True).all()
      await new_category.companies.add(*companies_to_add)
    return new_category

  except CustomError as e:
    raise e
    
  except Exception as e:
    logger.error(f"Unexpected error creating ticket category with data {category_data}: {e}", exc_info=True)
    raise CustomError(
      500,
      "Ocorreu um erro ao criar a categoria de tickets.",
      str(e)
    ) from e

async def fetch_ticket_categories(
  path: str,
  page_size: int,
  page: int,
  current_user: dict,
  search: str | None = None,
  and_filters: dict[str, any] | None = None,
  order_by: str | None = None,
  original_query_params: dict | None = None
  ) -> dict[str, any]:
  """
  Obtém uma lista paginada de categorias de tickets, com filtros e ordenação.

  Args:
    path (str): O caminho base da URL para links de paginação.
    page_size (int): O número de itens por página.
    page (int): O número da página atual.
    current_user (dict): O utilizador atual.
    search (str, opcional): Termo de pesquisa geral (OR) para campos como nome e descrição.
    and_filters (dict, opcional): Dicionário de filtros específicos (AND).
                                  Ex: {"name": "Support", "companies": 1}
    order_by (str, opcional): Campos para ordenação (ex: "name,-id").
    original_query_params (dict, opcional): Parâmetros originais da query para reconstruir URLs de paginação.

  Returns:
    dict[str, any]: Um dicionário com dados de paginação e a lista de categorias.

  Raises:
    CustomError: Se ocorrer algum erro durante a busca.
  """
  try:
    queryset = TicketCategories.filter(active=True)

    # Aplicar filtros AND
    if and_filters:
      for key, value in and_filters.items():
        if value is None or (isinstance(value, str) and not value.strip()): # Skip None or empty string values
            continue
        
        if key == "name":
          queryset = queryset.filter(name__icontains=value)
        elif key == "description":
          queryset = queryset.filter(description__icontains=value)
        elif key == "companies":
          if isinstance(value, list):
            if not all(isinstance(item, int) for item in value):
              logger.warning(f"Invalid company ID list in and_filters: {value}")
              continue
            queryset = queryset.filter(companies__id__in=value)
          elif isinstance(value, int):
            queryset = queryset.filter(companies__id=value)
          else:
            logger.warning(f"Invalid company ID type in and_filters: {value}")

    # Aplicar pesquisa OR
    if search:
      search_conditions = [
        Q(name__icontains=search),
        Q(description__icontains=search)
      ]
      combined_search_q = reduce(or_, search_conditions)
      queryset = queryset.filter(combined_search_q)
      
    # Aplicar ordenação
    if order_by:
      order_fields_input = order_by.split(',')
      valid_order_fields = []
      allowed_fields = ['id', 'name', 'description'] # Define campos permitidos para ordenação
      for field in order_fields_input:
        field_name = field.strip()
        actual_field_name = field_name.lstrip('-')
        if actual_field_name in allowed_fields:
          valid_order_fields.append(field_name)
        else:
          logger.warning(f"Ignored invalid order_by field: {field_name}")
      if valid_order_fields:
        queryset = queryset.order_by(*valid_order_fields)
    else:
      queryset = queryset.order_by('name') # Default order

    queryset = queryset.prefetch_related('companies', 'category_subcategories')

    paginated_result = await paginate(
      queryset=queryset,
      url=path,
      page=page,
      page_size=page_size,
      original_query_params=original_query_params
    )
    return paginated_result

  except CustomError as e:
    raise e
  
  except Exception as e:
    logger.error(f"Unexpected error fetching paginated ticket categories: {e}", exc_info=True)
    raise CustomError(
      500,
      "Ocorreu um erro ao obter a lista de categorias de tickets.",
      str(e)
    ) from e

async def fetch_all_ticket_categories(company_id: int | None = None) -> list[TicketCategories]:  
  """
  Obtém todas as categorias de tickets ativas.
  Opcionalmente, filtra as categorias por um ID de empresa.

  Returns:
    Uma lista de instâncias de TicketCategories.

  Args:
    company_id (int, opcional): O ID da empresa para filtrar as categorias.
                                 Se None, retorna todas as categorias ativas.

  Raises:
    CustomError: Se ocorrer algum erro durante a busca dos dados.
  """
  try:
    query = TicketCategories.filter(active=True)

    if company_id is not None:
      query = query.filter(companies__id=company_id)
      
    categories = await query.order_by('name').all()

    return categories

  except CustomError as e:
    raise e
    
  except Exception as e:
    logger.error(f"Unexpected error fetching ticket categories: {e}", exc_info=True)
    raise CustomError(
      500,
      "Ocorreu um erro ao obter as categorias de tickets.",
      str(e)
    ) from e

async def fetch_ticket_category_by_id(category_id: int) -> TicketCategories:
  """
  Obtém uma categoria de ticket pelo seu id.

  Args:
    category_id: O id da categoria de ticket a ser obtida.

  Returns:
    Um dicionário representando a categoria de ticket, incluindo suas empresas e subcategorias ativas.

  Raises:
    CustomError: Se a categoria não for encontrada ou se ocorrer algum erro durante a busca.
  """
  try:
    category_orm = await TicketCategories.filter(id=category_id, active=True).prefetch_related('companies', 'category_subcategories').first()
    if not category_orm:
      raise CustomError(404, "Categoria de ticket não encontrada", f"Nenhuma categoria encontrada com o ID: {category_id}")
    return await category_orm.to_dict()

  except CustomError as e:
    raise e
    
  except Exception as e:
    logger.error(f"Unexpected error fetching ticket category with ID {category_id}: {e}", exc_info=True)
    raise CustomError(
      500,
      "Ocorreu um erro ao buscar a categoria de ticket.",
      str(e)
    ) from e

async def update_ticket_category(category_id: int, category_data: dict) -> TicketCategories:
  """
  Atualiza os dados de uma categoria de ticket existente pelo id. 
  Também pode criar novas subcategorias associadas a esta categoria.

  Args:
    category_id: O id da categoria a ser atualizada.
    category_data: Um dicionário com os dados a serem atualizados.
                   Parâmetros esperados: 'name', 'description' (opcional),
                   'companies' (Opcional: lista de ids de empresas para substituir as existentes),
                   'subcategories_to_create' (Opcional: lista de nomes de subcategorias a serem criadas).

  Returns:
    A instância da categoria de ticket atualizada.

  Raises:
    CustomError: Se a categoria não for encontrada,
                 se uma categoria com o novo nome já existir,
                 se houver um erro ao criar uma subcategoria (ex: nome duplicado),
                 ou se ocorrer algum erro durante a atualização.
  """
  try:
    category_to_update = await TicketCategories.get_or_none(id=category_id, active=True)
    if not category_to_update:
      raise CustomError(404, "Categoria de ticket não encontrada", f"Nenhuma categoria encontrada com o id: {category_id}")

    # Valida o novo nome da categoria se for fornecido e diferente do atual
    new_name = category_data.get('name')
    if new_name and new_name != category_to_update.name:
      await _validate_category_name(new_name, category_id)

    company_ids = category_data.pop('companies', None)
    subcategories = category_data.pop('subcategories', None)

    # Atualiza os campos da categoria com os novos dados
    for key, value in category_data.items():
      setattr(category_to_update, key, value)
    await category_to_update.save()

    # Atualiza as empresas associadas, se fornecido
    if company_ids is not None: # "is not None" para permitir enviar uma lista vazia para remover todas as empresas
      await category_to_update.companies.clear() # Remove todas as associações existentes
      if company_ids: # Se a lista não estiver vazia, adiciona as novas
        companies_to_add = await Companies.filter(id__in=company_ids, active=True).all()
        if companies_to_add:
          await category_to_update.companies.add(*companies_to_add)

    # Cria novas subcategorias, se fornecido
    if subcategories:
      for sub_name in subcategories:
        if not isinstance(sub_name, str) or not sub_name.strip():
          logger.warning(f"Nome de subcategoria inválido fornecido: '{sub_name}'. Ignorando.")
          continue
        try:
          await TicketSubcategories.create(name=sub_name.strip(), category=category_to_update)
          logger.info(f"Subcategoria '{sub_name.strip()}' criada para a categoria ID {category_id}")
        except Exception as sub_exc:
          logger.error(f"Falha ao criar subcategoria '{sub_name.strip()}' para a categoria ID {category_id}: {sub_exc}", exc_info=True)
          raise CustomError(
            400, 
            f"Erro ao criar subcategoria '{sub_name.strip()}'. Verifique se já existe ou se o nome é válido.",
            str(sub_exc)
          ) from sub_exc

    return category_to_update

  except CustomError as e:
    raise e
  
  except Exception as e:
    logger.error(f"Unexpected error updating ticket category with ID {category_id} with data {category_data}: {e}", exc_info=True)
    raise CustomError(
      500,
      "Ocorreu um erro ao atualizar a categoria de ticket.",
      str(e)
    )

async def delete_ticket_category(category_id: int) -> None:
  """
  Marca uma categoria de ticket como inativa (soft delete).

  Args:
    category_id: O id da categoria a ser marcada como inativa.

  Raises:
    CustomError: Se a categoria não for encontrada ou se ocorrer um erro durante a operação.
  """
  try:
    category_to_delete = await TicketCategories.get_or_none(id=category_id, active=True)
    if not category_to_delete:
      raise CustomError(404, "Categoria de ticket não encontrada", f"Nenhuma categoria encontrada com o id: {category_id}")

    category_to_delete.active = False
    await category_to_delete.save()
  
  except CustomError as e:
    raise e
    
  except Exception as e:
    raise CustomError(
      500,
      "Ocorreu um erro ao marcar a categoria de ticket como inativa.",
      str(e)
    ) from e
