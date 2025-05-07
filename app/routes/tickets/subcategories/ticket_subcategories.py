from fastapi import APIRouter, Depends
from app.controllers.tickets.subcategories.ticket_subcategories import (
  handle_delete_ticket_subcategory,
)
from app.utils.helpers.token import validate_access_token
from app.services.users import require_permission


router = APIRouter(prefix="/ticket-subcategories", tags=["Ticket Subcategories"])

@router.delete("", status_code=204, dependencies=[Depends(require_permission("tecnico"))])
def delete_ticket_subcategory(subcategory_id: int, _= Depends(validate_access_token)):
  try:
    return handle_delete_ticket_subcategory(subcategory_id)
  except Exception as e:
    raise e