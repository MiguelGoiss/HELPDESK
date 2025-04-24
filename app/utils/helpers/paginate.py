from tortoise.queryset import QuerySet
from math import ceil
from urllib.parse import urlencode

async def paginate(
  queryset: QuerySet,
  url: str,
  page: int = 1,
  page_size: int = 10,
  # Pass original request query params to preserve filters/sorting in links
  original_query_params: dict[str, any] | None = None
) -> dict[str, any]:
  # O count deve acontecer no filtro/order antes do limit/offset
  total_count = await queryset.count()
  total_pages = ceil(total_count / page_size) if page_size > 0 else 0

  # Aplicar limit and offset para obter os dados
  dbData = await queryset.offset((page - 1) * page_size).limit(page_size)
  
  # Constroi a resposta com os dados prefetched
  data_list = [await data.to_dict() for data in dbData]
  
  # Geração do link
  base_params = original_query_params.copy() if original_query_params else {}

  def build_page_url(page_num):
    if not (1 <= page_num <= total_pages):
      return None
    params = base_params.copy()
    params['page'] = page_num
    params['page_size'] = page_size
    # urlencode lida com caracteres especiais e junta com "&"
    return f"{url}?{urlencode(params, doseq=True)}"

  return {
    "data": data_list,
    "total_count": total_count,
    "page": page,
    "page_size": page_size,
    "total_pages": total_pages,
    "next_page": build_page_url(page + 1),
    "previous_page": build_page_url(page - 1),
  }