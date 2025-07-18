from fastapi import HTTPException, Depends, Request
from app.services.users import (
  create_user,
  get_users,
  get_user_details,
  update_user_details,
  delete_user_details,
  user_authentication,
  fetch_email_user,
  code_verification,
  update_user_password,
  get_employees_with_permission,
  require_permission,
  create_token,
  fetch_all_user_permissions,
  fetch_requester_employees,
  authentication_test,
  validate_employee_existance,
  fetch_current_user,
  fetch_agents,
  fetch_gateway_user,
  fetch_equipment_users,
  filtered_user_ids_by_and_search,
)
from app.services.emails.emails import recovery_email
from fastapi.responses import JSONResponse
import json

async def add_user(user: dict, current_user: dict):
  try:
    new_user = await create_user(user, current_user)
    return JSONResponse(new_user, 200)
  
  except Exception as e:
    raise e

async def handle_fetch_users(
  path: str,
  page: int,
  page_size: int,
  original_query_params: dict,
  search: str,
  and_filters: str,
  order_by: str
):
  try:
    parsed_and_filters = {}
    if and_filters:
      try:
        parsed_and_filters = json.loads(and_filters)
        if not isinstance(parsed_and_filters, dict):
          raise ValueError("Parsed JSON is not a dictionary.")
      except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
          status_code=400,
          detail=f"Invalid format for 'and_filters' parameter. Expected a valid JSON object string. Error: {e}"
        )
      
    return await get_users(
      path,
      page,
      page_size,
      original_query_params,
      search,
      parsed_and_filters,
      order_by
    ) 
  except Exception as e:
    raise e

async def fetch_user_details(id: int):
  try:
    return await get_user_details(id)
  except Exception as e:
    raise e

async def update_user(id: int, user_data: dict, current_user: dict):
  try:
    return await update_user_details(id, user_data, current_user)
  except Exception as e:
    raise e

async def delete_user(id: int, current_user: dict):
  try:
    return await delete_user_details(id, current_user)
  except Exception as e:
    raise e

async def handle_user_authentication(authentication_form: dict):
  try:
    return await user_authentication(authentication_form)
  except Exception as e:
    raise e

async def handle_request_email_recovery(email: dict):
  try:
    db_user = await fetch_email_user(email.email)
    await recovery_email(db_user)
    return db_user

  except Exception as e:
    raise e

async def handle_code_verification(code: dict):
  try:
    db_user = await code_verification(code)
    return db_user
  except Exception as e:
    raise e

async def handle_password_recovery(recovery_form: dict):
  try:
    await code_verification(recovery_form)
    db_user = await update_user_password(recovery_form)
    return db_user
  except Exception as e:
    raise e

async def handle_get_employees_with_permission(permission_id: int, search: str | None = None):
  try:
    return await get_employees_with_permission(permission_id, search)
  except Exception as e:
    raise e

async def handle_access_token_creation(user_id: int):
  try:
    user_info = await fetch_user_details(user_id)
    new_access_token = await create_token(user_info)
    return JSONResponse({"access_token": new_access_token}, 200)
  except Exception as e:
    raise e

async def handle_fetch_all_user_permissions():
  try:
    return await fetch_all_user_permissions()
  except Exception as e:
    raise e

async def handle_fetch_requester_employees(company_id: int | None):
  try:
    return await fetch_requester_employees(company_id)
  except Exception as e:
    raise e

async def handle_authentication_test(authentication_form: dict):
  try:
    return await authentication_test(authentication_form)
  except Exception as e:
    raise e

async def handle_validate_employee_existance(employee_id: int):
  try:
    return await validate_employee_existance(employee_id)
  except Exception as e:
    raise e

async def handle_fetch_current_user(request: Request):
  try:
    employee_id: int | None = getattr(request.state, "user_id", None)
    return await fetch_current_user(employee_id)
  except Exception as e:
    raise e

async def handle_fetch_agents():
  try:
    return await fetch_agents()
  except Exception as e:
    raise e
  
async def test_user_gateway(request: Request):
  try:
    employee_id: int | None = getattr(request.state, "user_id", None)
    return await fetch_gateway_user(employee_id)
  except Exception as e:
    raise

async def handle_fetch_equipment_users(
    and_filters: str | None,
    order_by: str | None,
    ids_only: bool = False
  ):
  try:
    parsed_and_filters = {}
    if and_filters:
      try:
        parsed_and_filters = json.loads(and_filters)
        if not isinstance(parsed_and_filters, dict):
          raise ValueError("Parsed JSON is not a dictionary.")
      except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
          status_code=400,
          detail=f"Invalid format for 'and_filters' parameter. Expected a valid JSON object string. Error: {e}"
        )
    if ids_only:
      return await filtered_user_ids_by_and_search(
        parsed_and_filters,
        order_by
      ) 
    return await fetch_equipment_users(
      parsed_and_filters,
      order_by
    ) 
  except Exception as e:
    raise e
  