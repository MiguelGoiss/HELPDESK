from app.services.tickets.assistance_types.ticket_assistance_types import (
  fetch_ticket_assistance_types,
)
from app.utils.errors.exceptions import CustomError

async def handle_fetch_ticket_assistance_types():
  try:
    return await fetch_ticket_assistance_types()

  except CustomError as e:
    raise e

  except Exception as e:
    raise CustomError(
      500,
      "Ocorreu um erro a obter o tipo de assistencia do ticket.",
      str(e)
    ) from e