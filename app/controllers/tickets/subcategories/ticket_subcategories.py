from app.services.tickets.subcategories.ticket_subcategories import (
  delete_ticket_subcategory,
)
from app.utils.errors.exceptions import CustomError

async def handle_delete_ticket_subcategory(subcategory_id: int):
  try:
    return await delete_ticket_subcategory(subcategory_id)

  except CustomError as e:
    raise e

  except Exception as e:
    raise CustomError(
      500,
      "Ocorreu um erro a eliminar a categoria do ticket.",
      str(e)
    ) from e