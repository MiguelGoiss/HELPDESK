from fastapi import Depends, UploadFile, File
from fastapi.responses import JSONResponse
from app.services.tickets import create_ticket
from app.utils.errors.exceptions import CustomError
from app.schemas.tickets import BaseCreateTicket
import logging

logger = logging.getLogger(__name__)

async def handle_ticket_creation(
  ticket_data: BaseCreateTicket, # Receive the validated Pydantic model
  files: list[UploadFile] | None, # Receive the list of files (or None)
  current_user: dict | None = None
):
  """
  Controller function to handle the logic of ticket creation,
  including passing files to the service layer.
  """
  try:
    logger.info(f"Handling ticket creation request by user: {current_user.get('id') if current_user else 'anonymous'}")
    # Pass the ticket data and files to the service function
    new_ticket_details = await create_ticket(
      ticket_data=ticket_data,
      current_user=current_user,
      files=files
    )
    logger.info(f"Ticket created successfully. Details: {new_ticket_details}")
    # Return the result (e.g., details of the created ticket)
    # The service already returns ticket_log_details_filtered
    return new_ticket_details
  except CustomError as e:
      # Re-raise CustomErrors to be handled by FastAPI exception handlers
      logger.error(f"CustomError during ticket creation: {e.detail}", exc_info=True)
      raise e
  except Exception as e:
    # Catch unexpected errors, log them, and raise a generic CustomError
    # or let FastAPI's default 500 handler catch it.
    logger.error(f"Unexpected error during ticket creation: {e}", exc_info=True)
    # You might want to raise a more specific error or just re-raise
    # raise CustomError(status_code=500, detail="An unexpected error occurred during ticket creation.") from e
    raise e # Re-raising allows FastAPI's handlers to manage it
