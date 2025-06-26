import logging
from app.database.models.helpdesk import TicketStatuses
from app.utils.errors.exceptions import CustomError

logger = logging.getLogger(__name__)

async def fetch_ticket_statuses():
  try:
    db_status = await TicketStatuses.all()
    return [status.to_dict() for status in db_status]
  except Exception as e:
    raise CustomError(
      500,
      "Ocorreu um erro a obter os estados do ticket",
      str(e)
    )