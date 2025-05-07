from app.services.tickets.types.ticket_types import (
  fetch_ticket_types,
)
from app.utils.errors.exceptions import CustomError

async def handle_fetch_ticket_types():
  try:
    return await fetch_ticket_types()

  except CustomError as e:
    raise e

  except Exception as e:
    raise CustomError(
      500,
      "Ocorreu um erro a obter os tipos de ticket.",
      str(e)
    ) from e