from app.services.tickets.status import (
  fetch_ticket_statuses,
)
from app.utils.errors.exceptions import CustomError

async def handle_fetch_ticket_statuses():
  try:
    return await fetch_ticket_statuses()

  except CustomError as e:
    raise e

  except Exception as e:
    raise CustomError(
      500,
      "Ocorreu um erro a obter os tipos de ticket.",
      str(e)
    ) from e