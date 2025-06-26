from fastapi import Depends, UploadFile
from fastapi.responses import JSONResponse
from app.services.tickets import (
  create_ticket,
  fetch_tickets,
  fetch_ticket_details,
  update_ticket_details,
  fetch_preset_counts,
  fetch_ticket_logs,
  fetch_ticket_file,
)
from app.utils.errors.exceptions import CustomError
from app.schemas.tickets import BaseCreateTicket
import logging
import json

logger = logging.getLogger(__name__)

async def handle_ticket_creation(
  ticket_data: BaseCreateTicket,
  files: list[UploadFile] | None = None,
  current_user: dict | None = None
):
  try:
    logger.info(f"Handling ticket creation request by user: {current_user.get('id') if current_user else 'anonymous'}")
    new_ticket_details = await create_ticket(
      ticket_data=ticket_data,
      current_user=current_user,
      files=files
    )
    logger.info(f"Ticket created successfully. Details: {new_ticket_details}")
    return new_ticket_details
  except CustomError as e:
      logger.error(f"CustomError during ticket creation: {e.detail}", exc_info=True)
      raise e
  except Exception as e:
    logger.error(f"Unexpected error during ticket creation: {e}", exc_info=True)
    raise e

async def handle_fetch_tickets(
  path: str,
  page: int,
  page_size: int,
  original_query_params: dict,
  current_user: dict,
  own: bool,
  search: str | None,
  and_filters: str | None,
  order_by: str | None,
):
  try:
    logger.info(f"Handling fetch tickets request. Page: {page}, Page Size: {page_size}, Search: '{search}', Order By: '{order_by}'")
    logger.debug(f"Raw and_filters string: {and_filters}")

    parsed_and_filters = None
    if and_filters:
      try:
        parsed_and_filters = json.loads(and_filters)
        if not isinstance(parsed_and_filters, dict):
          raise ValueError("Parsed JSON is not a dictionary")
        logger.debug(f"Parsed and_filters: {parsed_and_filters}")
      except (json.JSONDecodeError, ValueError) as json_error:
        logger.error(f"Failed to parse and_filters JSON string: {and_filters}. Error: {json_error}", exc_info=True)
        raise CustomError(400, f"Invalid format for 'and_filters'. Expected a valid JSON object string. Error: {json_error}")

    tickets_result = await fetch_tickets(
      path=path,
      page=page,
      page_size=page_size,
      original_query_params=original_query_params,
      search=search,
      and_filters=parsed_and_filters,
      order_by=order_by,
      current_user=current_user,
      own=own,
    )
    logger.info(f"Successfully fetched tickets. Page: {page}, Count: {len(tickets_result.get('items', []))}")
    return tickets_result

  except CustomError as e:
    logger.error(f"CustomError during fetching tickets: Status={e.status_code}, Detail={e.detail}", exc_info=True)
    raise e

  except Exception as e:
    logger.error(f"Unexpected error during fetching tickets: {e}", exc_info=True)
    raise e
  
async def handle_fetch_ticket_details(
  uid: str,
  current_user: dict | None = None
):
  try:
    db_ticket_details = await fetch_ticket_details(uid)
    return db_ticket_details
  except CustomError as e:
    raise e
  except Exception as e:
    raise e

async def handle_update_ticket(
  uid: str,
  ticket_data: dict,
  current_user: dict,
  files: list[UploadFile] | None = None
):
  try:
    logger.info(f"Handling ticket update request by user: {current_user.get('id')}")
    updated_ticket_details = await update_ticket_details(
      uid,
      ticket_data,
      current_user,
      files,
    )
    return updated_ticket_details
  except CustomError as e:
    raise e
  except Exception as e:
    raise e
    
async def handle_preset_counts(
  current_user: dict,
  search: str | None = None,
  and_filters: str | None = None,
  own: bool | None = False,
):
  presets_count = await fetch_preset_counts(search, and_filters, own, current_user)
  return presets_count

async def handle_fetch_ticket_logs(
  uid: str
):
  try:
    ticket_logs = await fetch_ticket_logs(uid)
    return ticket_logs
  except CustomError as e:
    logger.error(f"CustomError during fetching tickets: Status={e.status_code}, Detail={e.detail}", exc_info=True)
    raise e

  except Exception as e:
    logger.error(f"Unexpected error during fetching tickets: {e}", exc_info=True)
    raise e

async def handle_fetch_ticket_file(
  uid: str,
  filename: str,
):
  try:
    return await fetch_ticket_file(uid, filename)
    
  except CustomError as e:
    raise e
  
  except Exception as e:
    raise e

