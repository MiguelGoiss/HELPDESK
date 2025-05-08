from app.database.models.helpdesk import TicketCategories, TicketSubcategories
from app.utils.errors.exceptions import CustomError
from tortoise.queryset import QuerySet
from ...filtering import (
  _apply_and_filters,
  _apply_or_search,
  _apply_ordering, 
)

async def _validate_category_name(category_name: str, category_id: int | None = None):
  """
  Valida se o nome da categoria já existe na base de dados.

  Args:
    category_name: O nome da categoria a ser validado.
    category_id: O id da categoria a ser ignorada na verificação (para updates).

  Raises:
    CustomError: Se o nome da categoria já existir ou ocorrer algum erro durante a busca.
  """
  try:
    if category_id:
      existing_category = await TicketCategories.get_or_none(name=category_name, active=True).exclude(id=category_id)
    else:
      existing_category = await TicketCategories.get_or_none(name=category_name, active=True)
    if not existing_category:
      return True
    
    raise CustomError(
      409,
      "Uma categoria com o nome inserido já existe",
      f"Uma categoria com o nome: {category_name} já existe criado com o id: {existing_category.id}"
    )
  except Exception as e:
    raise CustomError(
      500,
      "Ocorreu um erro ao validar o nome da categoria inserido",
      str(e)
    )

# --- Configuração dos campos permitidos para pesquisas e order by ---
# Campos permitidos para a pesquisa geral 'search' (OR)
DEFAULT_OR_SEARCH_FIELDS: list[str] = ['id', 'name', 'description']

# Campos permitidos para o search (AND)
ALLOWED_AND_FILTER_FIELDS: set[str] = {
  'id', 'name', 'description', 'companies__id'
}

# Campos permitidos para order
ALLOWED_ORDER_FIELDS: set[str] = {
  'id', 'name'
}
# --- Fim da Configuração ---

def _apply_filters(
  queryset: QuerySet,
  filters_dict: dict[str, any] | None,
  search: str | None,
  order_by: str | None
) -> QuerySet:

  if filters_dict:
    queryset = _apply_and_filters(queryset, None, ALLOWED_AND_FILTER_FIELDS, filters_dict)
  
  if search:
    queryset = _apply_or_search(queryset, DEFAULT_OR_SEARCH_FIELDS, search)

  queryset = _apply_ordering(queryset, ALLOWED_ORDER_FIELDS, "-id", order_by)
  
  return queryset