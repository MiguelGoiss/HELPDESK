from fastapi import APIRouter, Request, Query, Depends
from app.schemas.tickets.categories.ticket_categories import BaseCreateTicketCategory, BaseUpdateTicketCategory
from app.controllers.tickets.categories.ticket_categories import (
  handle_create_ticket_category,
  handle_fetch_ticket_categories,
  handle_fetch_all_ticket_categories,
  handle_fetch_ticket_category_by_id,
  handle_update_ticket_category,
  handle_delete_ticket_category,
)
from app.utils.helpers.token import validate_access_token
from app.services.users import require_permission


router = APIRouter(prefix="/ticket-categories", tags=["Ticket Categories"])

@router.post("", status_code=201, dependencies=[Depends(require_permission("tecnico"))])
async def create_ticket_category(
  category_data: BaseCreateTicketCategory,
  current_user: dict = Depends(validate_access_token)
):
  return await handle_create_ticket_category(category_data.model_dump())

@router.get("")
async def read_ticket_categories(company_id:int | None = None):
  return await handle_fetch_all_ticket_categories(company_id)

@router.get("/details", dependencies=[Depends(require_permission("tecnico"))])
async def read_tickets(
  request: Request,
  page: int = Query(1, ge=1, description="Page number"),
  page_size: int = Query(100, ge=1, le=100, description="Items per page"),
  current_user: dict = Depends(validate_access_token),
  search: str | None = None,
  and_filters: str | None = None,
  order_by: str | None = None,
):
  query_params = dict(request.query_params)
  tickets_data = await handle_fetch_ticket_categories(
    request.url.path,
    page_size,
    page,
    current_user,
    search,
    and_filters,
    order_by,
    query_params,
  )
  return tickets_data

@router.get("/details/{category_id}", dependencies=[Depends(require_permission("tecnico"))])
async def read_ticket_category_by_id(
  category_id: int,
  _: dict = Depends(validate_access_token)
):
  return await handle_fetch_ticket_category_by_id(category_id)

@router.put("/details/{category_id}", dependencies=[Depends(require_permission("tecnico"))])
async def update_ticket_category(
  category_id: int,
  category_data: BaseUpdateTicketCategory,
  current_user: dict = Depends(validate_access_token)
):
  return await handle_update_ticket_category(category_id, category_data.model_dump(exclude_unset=True))

@router.delete("/details/{category_id}", status_code=204, dependencies=[Depends(require_permission("tecnico"))])
async def delete_ticket_category(
  category_id: int,
  current_user: dict = Depends(validate_access_token)
):
  return await handle_delete_ticket_category(category_id)