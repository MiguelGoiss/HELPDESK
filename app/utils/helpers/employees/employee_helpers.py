from tortoise.queryset import QuerySet
from ..filtering import (
  _apply_and_filters,
  _apply_or_search,
  _apply_ordering, 
)

# --- Configuração dos campos permitidos para pesquisas e order by ---
# Campos permitidos para a pesquisa geral 'search' (OR)
DEFAULT_OR_SEARCH_FIELDS: list[str] = ['id', 'first_name', 'last_name', 'full_name', 'employee_num']

# Campos permitidos para o search (AND)
ALLOWED_AND_FILTER_FIELDS: set[str] = {
  'id', 'first_name', 'last_name', 'full_name', 'employee_num',
  'username', 'email', 'department_id', 'company_id', 'local_id',
  'department__name', 'company__name', 'local__name'
}

# Campos permitidos para order
ALLOWED_ORDER_FIELDS: set[str] = {
  'id', 'first_name', 'last_name', 'full_name', 'employee_num',
  'created_at', 'updated_at', 'last_time_seen',
  'department__name', 'company__name', 'local__name',
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