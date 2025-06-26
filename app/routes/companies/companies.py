from fastapi import APIRouter, Depends, Request, Query
from app.controllers.companies.companies import (
  handle_fetch_companies,
  handle_create_company,
  handle_fetch_companies_management,
  handle_fetch_company_by_id,
  handle_update_company_details,
  handle_deactivate_company,
)
from app.controllers.users import handle_fetch_current_user
from app.schemas.companies.companies import (
  CompanyCreation,
  CompanyUpdate,
)
from app.services.users import fetch_current_user

router = APIRouter(prefix="/companies", tags=["Companies"])

@router.get("")
async def fetch_companies():
  try:
    return await handle_fetch_companies()
  except Exception as e:
    raise e

@router.post("", status_code=201)
async def create_new_company(company_data: CompanyCreation, current_user: dict = Depends(handle_fetch_current_user)):
  """
  Cria uma nova empresa, com locais e categorias de ticket se fornecidos.
  """
  try:
    return await handle_create_company(company_data)
  except Exception as e:
    raise e

# TODO Falta documentar isto
@router.get("/details")
async def fetch_companies_management(
  request: Request,
  page: int = Query(1, ge=1, description="Page number"),
  page_size: int = Query(100, ge=1, le=100, description="Items per page"),
  search: str | None = None,
  and_filters: str | None = None,
  order_by: str | None = None,
):
  query_params = dict(request.query_params)
  companies_data = await handle_fetch_companies_management(
    request.url.path,
    page,
    page_size,
    query_params,
    search,
    and_filters,
    order_by,
  )
  return companies_data

@router.get("/details/{company_id}")
async def get_company_by_id(company_id: int):
  """
  Obtém os detalhes de uma empresa pelo id.
  """
  try:
    return await handle_fetch_company_by_id(company_id)
  except Exception as e:
    raise e

@router.put("/details/{company_id}")
async def update_existing_company(company_id: int, company_data: CompanyUpdate, current_user: dict = Depends(handle_fetch_current_user)):
  """
  Atualiza os detalhes de uma empresa.
  """
  try:
    return await handle_update_company_details(company_id, company_data)
  except Exception as e:
    raise e

@router.delete("/details/{company_id}", status_code=204)
async def deactivate_existing_company(company_id: int, current_user: dict = Depends(handle_fetch_current_user)):
  """
  Desativa uma empresa.
  """
  try:
    return await handle_deactivate_company(company_id)
  except Exception as e:
    raise e