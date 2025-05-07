import logging
from app.database.models.helpdesk import TicketAssistanceTypes
from app.utils.errors.exceptions import CustomError

logger = logging.getLogger(__name__)

async def fetch_ticket_assistance_types() -> list[dict]:
  """
  Obtém todos os tipos de assistência de ticket ativos.

  Returns:
    Uma lista de dicionários, onde cada dicionário representa um tipo de assistência.

  Raises:
    CustomError: Se ocorrer algum erro durante a busca dos dados.
  """
  try:
    assistance_types_orm = await TicketAssistanceTypes.filter(active=True).order_by('name').all()
    return [assistance_type.to_dict() for assistance_type in assistance_types_orm]

  except Exception as e:
    logger.error(f"Unexpected error fetching ticket assistance types: {e}", exc_info=True)
    raise CustomError(
      500,
      "Ocorreu um erro ao obter os tipos de assistência de tickets.",
      str(e)
    ) from e

