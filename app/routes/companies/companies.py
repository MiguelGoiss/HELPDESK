from fastapi import APIRouter, status, Depends
from app.controllers.companies.companies import (
  handle_fetch_companies,
  handle_create_company,
  handle_fetch_company_by_id,
  handle_update_company_details,
  handle_deactivate_company,
)
from app.schemas.companies.companies import (
  CompanyCreation,
  CompanyUpdate,
)
from app.services.users.auth import require_permission
from app.utils.helpers.token import validate_access_token

router = APIRouter(prefix="/companies", tags=["Companies"])

@router.get("")
async def fetch_companies():
  try:
    return await handle_fetch_companies()
  except Exception as e:
    raise e

@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("tecnico"))])
async def create_new_company(company_data: CompanyCreation, current_user: dict = Depends(validate_access_token)):
  """
  Cria uma nova empresa, com locais e categorias de ticket se fornecidos.
  """
  try:
    return await handle_create_company(company_data)
  except Exception as e:
    raise e

@router.get("/details/{company_id}", dependencies=[Depends(require_permission("tecnico"))])
async def get_company_by_id(company_id: int, _: dict = Depends(validate_access_token)):
  """
  Obtém os detalhes de uma empresa pelo id.
  """
  try:
    return await handle_fetch_company_by_id(company_id)
  except Exception as e:
    raise e

@router.put("/details/{company_id}", dependencies=[Depends(require_permission("tecnico"))])
async def update_existing_company(company_id: int, company_data: CompanyUpdate, current_user: dict = Depends(validate_access_token)):
  """
  Atualiza os detalhes de uma empresa.
  """
  try:
    return await handle_update_company_details(company_id, company_data)
  except Exception as e:
    raise e

@router.delete("/details/{company_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("tecnico"))])
async def deactivate_existing_company(company_id: int, current_user: dict = Depends(validate_access_token)):
  """
  Desativa uma empresa.
  """
  try:
    return await handle_deactivate_company(company_id)
  except Exception as e:
    raise e