from fastapi import APIRouter, Path, Request, Query
from app.controllers.departments.departments import (
  handle_create_department,
  handle_fetch_departments,
  handle_fetch_departments_management,
  handle_fetch_department_by_id,
  handle_update_department_details,
  handle_deactivate_department,
)
from app.schemas.departments import DepartmentCreation, DepartmentsUpdate

router = APIRouter(prefix="/departments", tags=["Departments"])

@router.post("", status_code=201)
async def create_new_department(department_data: DepartmentCreation):
  """
  Creates a new department.
  The request body should conform to the structure expected by `create_department` service.
  Example: `{"name": "IT Support", "company_ids": [1, 2]}`
  """
  try:
    return await handle_create_department(department_data)
  except Exception as e:
    raise e

@router.get("")
async def get_all_departments():
  """
  Fetches all departments.
  """
  try:
    return await handle_fetch_departments()
  except Exception as e:
    raise e

@router.get("/details")
async def fetch_departments_management(
  request: Request,
  page: int = Query(1, ge=1, description="Page number"),
  page_size: int = Query(100, ge=1, le=100, description="Items per page"),
  search: str | None = None,
  and_filters: str | None = None,
  order_by: str | None = None,
):
  query_params = dict(request.query_params)
  companies_data = await handle_fetch_departments_management(
    request.url.path,
    page,
    page_size,
    query_params,
    search,
    and_filters,
    order_by,
  )
  return companies_data

@router.get("/details/{department_id}")
async def get_department_by_id(department_id: int = Path(..., title="The ID of the department to get")):
  """
  Fetches a specific department by its ID.
  """
  try:
    return await handle_fetch_department_by_id(department_id)
  except Exception as e:
    raise e

@router.put("/details/{department_id}")
async def update_existing_department(department_data: DepartmentsUpdate, department_id: int = Path(..., title="The ID of the department to update")):
  """
  Updates an existing department's details.
  The request body should contain the fields to be updated.
  Example: `{"name": "Information Technology", "company_ids": [1]}`
  """
  try:
    return await handle_update_department_details(department_id, department_data)
  except Exception as e:
    raise e

@router.delete("/details/{department_id}", status_code=204)
async def deactivate_existing_department(department_id: int = Path(..., title="The ID of the department to deactivate")):
  """
  Deactivates a department.
  """
  try:
    return await handle_deactivate_department(department_id)
  except Exception as e:
    raise e