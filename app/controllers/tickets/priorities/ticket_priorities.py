from app.services.tickets.priorities.ticket_priorities import (
  fetch_ticket_priorities,
)
from app.utils.errors.exceptions import CustomError

async def handle_fetch_ticket_priorities():
  try:
    return await fetch_ticket_priorities()

  except CustomError as e:
    raise e

  except Exception as e:
    raise CustomError(
      500,
      "Ocorreu um erro a obter os tipos de ticket.",
      str(e)
    ) from e