import logging
from app.database.models.helpdesk import TicketTypes
from app.utils.errors.exceptions import CustomError

logger = logging.getLogger(__name__)

async def fetch_ticket_types() -> list[dict]:
  """
  Obtém todos os tipos de ticket.

  Returns:
    Uma lista de dicionários, onde cada dicionário representa um tipo de ticket.

  Raises:
    CustomError: Se ocorrer algum erro durante a busca dos dados.
  """
  try:
    ticket_types_orm = await TicketTypes.all().order_by('name')
    return [ticket_type.to_dict() for ticket_type in ticket_types_orm]

  except Exception as e:
    logger.error(f"Unexpected error fetching ticket types: {e}", exc_info=True)
    raise CustomError(
      500,
      "Ocorreu um erro ao obter os tipos de tickets.",
      str(e)
    ) from e
  