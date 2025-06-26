from tortoise.queryset import QuerySet
from tortoise import Tortoise
from math import ceil
from urllib.parse import urlencode
import time

async def paginate(
  queryset: QuerySet,
  url: str,
  page: int = 1,
  page_size: int = 10,
  # Pass original request query params to preserve filters/sorting in links
  original_query_params: dict[str, any] | None = None,
  distinct: bool = False
) -> dict[str, any]:
  start_time = time.time()
  # O count deve acontecer no filtro/order antes do limit/offset
  if distinct:
    total_count = len(await queryset.all())
  else:
    total_count = await queryset.count()
    
  total_pages = ceil(total_count / page_size) if page_size > 0 else 0
  print("Despois do count:",time.time() - start_time)
  
  # Aplicar limit and offset para obter os dados
  dbData = await queryset.offset((page - 1) * page_size).limit(page_size)

  print(dbData)
  # Constroi a resposta com os dados prefetched
  data_list = [await data.to_dict_pagination() for data in dbData]
  print("Despois de serializar a resposta:",time.time() - start_time)
  
  # Geração do link
  base_params = original_query_params.copy() if original_query_params else {}

  def build_page_url(page_num):
    if not (1 <= page_num <= total_pages):
      return None
    params = base_params.copy()
    params['page'] = page_num
    params['page_size'] = page_size
    # urlencode lida com caracteres especiais e junta-os com "&"
    return f"{url}?{urlencode(params, doseq=True)}"

  print("final da função:",time.time() - start_time)
  return {
    "data": data_list,
    "total_count": total_count,
    "page": page,
    "page_size": page_size,
    "total_pages": total_pages,
    "next_page": build_page_url(page + 1)[7:] if page < total_pages else None, # dá skip ao prefixo do endpoint
    "previous_page": build_page_url(page - 1)[7:] if page > 1 else None, # dá skip ao prefixo do endpoint
  }
