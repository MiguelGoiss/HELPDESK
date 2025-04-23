from fastapi import APIRouter, Request, Query, Depends, UploadFile, File
from app.schemas.tickets import BaseCreateTicket
from app.services.users import require_permission
from app.utils.helpers.token import validate_optional_access_token
from app.controllers.tickets import (
  handle_ticket_creation,
)

router = APIRouter(prefix="/tickets", tags=["Tickets"])

@router.post("/ApiV1/tickets")
async def create_ticket(
  ticket_data: BaseCreateTicket = Depends(BaseCreateTicket.as_form),
  files: list[UploadFile] | None = File(None),
  current_user: dict | None = Depends(validate_optional_access_token)
):
  
  return await handle_ticket_creation(
    ticket_data=ticket_data,
    files=files,
    current_user=current_user
  )
  
  
  