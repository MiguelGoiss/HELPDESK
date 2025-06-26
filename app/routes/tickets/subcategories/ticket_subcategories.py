from fastapi import APIRouter, Depends
from app.controllers.tickets.subcategories.ticket_subcategories import (
  handle_delete_ticket_subcategory,
)
from app.utils.helpers.token import validate_access_token
from app.services.users import require_permission


router = APIRouter(prefix="/ticket-subcategories", tags=["Ticket Subcategories"])

@router.delete("/details/{subcategory_id}", status_code=204)
async def delete_ticket_subcategory(subcategory_id: int):
  try:
    return await handle_delete_ticket_subcategory(subcategory_id)
  except Exception as e:
    raise e