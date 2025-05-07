import logging
from app.database.models.helpdesk import TicketPriorities
from app.utils.errors.exceptions import CustomError

logger = logging.getLogger(__name__)

async def fetch_ticket_priorities() -> list[dict]:
  """
  Obtém todas as prioridades de ticket ativas, ordenadas pelo nível.

  Returns:
    Uma lista de dicionários, onde cada dicionário representa uma prioridade de ticket.

  Raises:
    CustomError: Se ocorrer algum erro durante a busca dos dados.
  """
  try:
    priorities_orm = await TicketPriorities.all().order_by('-level')
    return [priority.to_dict() for priority in priorities_orm]

  except Exception as e:
    logger.error(f"Unexpected error fetching ticket priorities: {e}", exc_info=True)
    raise CustomError(
      500,
      "Ocorreu um erro ao obter as prioridades de tickets.",
      str(e)
    ) from e

  