from fastapi import APIRouter, Depends
from app.controllers.tickets.status import (
  handle_fetch_ticket_statuses,
)

router = APIRouter(prefix="/ticket-status", tags=["Ticket Status"])

@router.get("")
async def fetch_ticket_types():
  try:
    return await handle_fetch_ticket_statuses()
  except Exception as e:
    raise e