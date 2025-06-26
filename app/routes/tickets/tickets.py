from fastapi import APIRouter, Request, Query, Depends, UploadFile, File
from app.schemas.tickets import BaseCreateTicket, BaseUpdateTicket
from app.controllers.users import  handle_fetch_current_user
from app.utils.helpers.token import validate_optional_access_token, validate_access_token
from app.controllers.tickets import (
  handle_ticket_creation,
  handle_fetch_tickets,
  handle_fetch_ticket_details,
  handle_update_ticket,
  handle_preset_counts,
  handle_fetch_ticket_logs,
  handle_fetch_ticket_file,
)

router = APIRouter(prefix="/tickets", tags=["Tickets"])

@router.post("")
async def create_ticket(
  ticket_data: BaseCreateTicket = Depends(BaseCreateTicket.as_form),
  files: list[UploadFile] | None = File(None),
  current_user: dict | None = Depends(handle_fetch_current_user)
):
  return await handle_ticket_creation(
    ticket_data=ticket_data,
    files=files,
    current_user=current_user
  )

@router.get("")
async def read_tickets(
  request: Request,
  page: int = Query(1, ge=1, description="Page number"),
  page_size: int = Query(100, ge=1, le=100, description="Items per page"),
  current_user: dict = Depends(handle_fetch_current_user),
  own: bool | None = False,
  search: str | None = None,
  and_filters: str | None = None,
  order_by: str | None = None,
):
  query_params = dict(request.query_params)
  tickets_data = await handle_fetch_tickets(
    request.url.path,
    page,
    page_size,
    query_params,
    current_user,
    own,
    search,
    and_filters,
    order_by,
  )
  return tickets_data

@router.get("/details/{uid}")
async def get_ticket_details(
  uid: str
):
  ticket_details = await handle_fetch_ticket_details(uid)
  return ticket_details

@router.put("/details/{uid}")
async def update_ticket(
  uid: str,
  ticket_data: dict = Depends(BaseUpdateTicket.as_form),
  current_user: dict = Depends(handle_fetch_current_user),
  files: list[UploadFile] | None = File(None)
):
  updated_ticket = await handle_update_ticket(
    uid,
    ticket_data,
    current_user,
    files
  )
  return updated_ticket

@router.get("/presets")
async def get_ticket_presets_count(
  current_user: dict = Depends(handle_fetch_current_user),
  own: bool | None = False,
  and_filters: str | None = None,
  search: str | None = None,
):
  print(and_filters)
  ticket_presets = await handle_preset_counts(current_user, search, and_filters, own)
  return ticket_presets

@router.get("/details/{uid}/logs")
async def get_ticket_logs(
  uid: str
):
  ticket_logs = await handle_fetch_ticket_logs(uid)
  return ticket_logs

@router.get("/details/{uid}/files/{filename}")
async def get_ticket_file(
  uid: str,
  filename: str
):
  return await handle_fetch_ticket_file(uid, filename)

