from fastapi import APIRouter, Depends
from app.controllers.tickets.priorities.ticket_priorities import (
  handle_fetch_ticket_priorities,
)

router = APIRouter(prefix="/ticket-priorities", tags=["Ticket Priorities"])

@router.get("")
async def fetch_ticket_priorities():
  try:
    return await handle_fetch_ticket_priorities()
  except Exception as e:
    raise e