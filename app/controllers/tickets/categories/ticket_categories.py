from app.services.tickets.categories.ticket_categories import (
  create_ticket_category,
  fetch_ticket_categories,
  fetch_all_ticket_categories,
  fetch_ticket_category_by_id,
  update_ticket_category,
  delete_ticket_category,
)
from app.utils.errors.exceptions import CustomError

async def handle_create_ticket_category(category_data: dict):
  try:    
    return await create_ticket_category(category_data)
  
  except CustomError as e:
    raise e

  except Exception as e:
    raise CustomError(
      500,
      "Ocorreu um erro ao criar a categoria do ticket.",
      str(e)
    ) from e

async def handle_fetch_all_ticket_categories(company_id: int | None = None):
  try:
    return await fetch_all_ticket_categories(company_id)
  
  except CustomError as e:
    raise e

  except Exception as e:
    raise CustomError(
      500,
      "Ocorreu um erro a buscar as categorias dos tickets.",
      str(e)
    ) from e
    
async def handle_fetch_ticket_categories(
  path: str,
  page_size: int,
  page: int,
  current_user: dict,
  search: str | None = None,
  and_filters: dict[str, any] | None = None,
  order_by: str | None = None,
  original_query_params: dict | None = None
  ):
  
  try:
    return await fetch_ticket_categories(
      path,
      page_size,
      page,
      current_user,
      search,
      and_filters,
      order_by,
      original_query_params,
    )
  
  except CustomError as e:
    raise e

  except Exception as e:
    raise CustomError(
      500,
      "Ocorreu um erro a buscar as categorias dos tickets.",
      str(e)
    ) from e

async def handle_fetch_ticket_category_by_id(category_id: int):
  try:
    return await fetch_ticket_category_by_id(category_id)

  except CustomError as e:
    raise e

  except Exception as e:
    raise CustomError(
      500,
      "Ocorreu um erro a obter os detalhes da categoria do ticket pelo id.",
      str(e)
    ) from e

async def handle_update_ticket_category(category_id: int, category_data: dict):
  try:
    return await update_ticket_category(category_id, category_data)

  except CustomError as e:
    raise e

  except Exception as e:
    raise CustomError(
      500,
      "Ocorreu um erro ao atualizar a categoria do ticket.",
      str(e)
    ) from e

async def handle_delete_ticket_category(category_id: int):
  try:
    return await delete_ticket_category(category_id)

  except CustomError as e:
    raise e

  except Exception as e:
    raise CustomError(
      500,
      "Ocorreu um erro a eliminar a categoria do ticket.",
      str(e)
    ) from e


  