from fastapi import APIRouter, Depends
from app.controllers.tickets.assistance_types.ticket_assistance_types import (
  handle_fetch_ticket_assistance_types,
)

router = APIRouter(prefix="/ticket-assistance-types", tags=["Ticket Assitance Types"])

@router.get("")
async def fetch_ticket_assistance_types():
  try:
    return await handle_fetch_ticket_assistance_types()
  except Exception as e:
    raise e