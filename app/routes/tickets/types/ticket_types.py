from fastapi import APIRouter, Depends
from app.controllers.tickets.types.ticket_types import (
  handle_fetch_ticket_types,
)

router = APIRouter(prefix="/ticket-types", tags=["Ticket Types"])

@router.get("")
async def fetch_ticket_types():
  try:
    return await handle_fetch_ticket_types()
  except Exception as e:
    raise e