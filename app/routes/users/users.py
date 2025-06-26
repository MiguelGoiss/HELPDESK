from fastapi import APIRouter, Request, Query, Depends
from app.controllers.users import (
  add_user,
  handle_fetch_users,
  fetch_user_details,
  update_user,
  delete_user,
  handle_user_authentication,
  handle_request_email_recovery,
  handle_code_verification,
  handle_password_recovery,
  handle_get_employees_with_permission,
  handle_access_token_creation,
  handle_fetch_all_user_permissions,
  handle_fetch_requester_employees,
  handle_authentication_test,
  handle_validate_employee_existance,
  handle_fetch_current_user,
  handle_fetch_agents,
  test_user_gateway,
  handle_fetch_equipment_users,
)
from app.schemas.users import UserCreate, UserResponse, UserUpdate, UserAuthentication, EmailForm, CodeForm, RecoveryForm
from app.utils.helpers.token import validate_access_token, validate_refresh_token
from app.utils.keys import verify_jwt

router = APIRouter(prefix="/employees", tags=["Users"])

@router.post("", response_model=UserResponse)
async def create_user(user: UserCreate):
  return await add_user(user, {"id":1})

@router.get("")
async def read_users(
  request: Request,
  page: int = Query(1, ge=1, description="Page number"),
  page_size: int = Query(10, ge=1, le=100, description="Items per page"),
  and_filters: str | None = None,
  order_by: str | None = None,
  search: str | None = None,
):
  query_params = dict(request.query_params)
  users_data = await handle_fetch_users(
    path=request.url.path,
    page=page,
    page_size=page_size,
    original_query_params=query_params,
    search=search,
    and_filters=and_filters,
    order_by=order_by
  )
  return users_data

@router.get("/details/{id}")
async def get_user_details(id: int):
  return await fetch_user_details(id)

@router.put("/details/{id}")
async def update_user_details(id:int, user_data: UserUpdate, current_user: dict = Depends(handle_fetch_current_user)):
  return await update_user(id, user_data, current_user)

@router.delete("/details/{id}")
async def delete_user_details(id: int, current_user: dict = Depends(handle_fetch_current_user)):
  return await delete_user(id, current_user)

@router.get("/me")#, dependencies=[Depends(verify_jwt)])
async def read_user_me(current_user: dict = Depends(handle_fetch_current_user)):
  return current_user

@router.post("/authenticate")
async def authenticate_user(authentication_form: UserAuthentication):
  return await handle_user_authentication(authentication_form)

@router.post("/recovery-request")
async def request_password_recovery(email: EmailForm):
  return await handle_request_email_recovery(email)

@router.post("/verify-code")
async def verify_code(code: CodeForm):
  return await handle_code_verification(code)

@router.put("/password-recovery")
async def password_recovery(recovery_form: RecoveryForm):
  return await handle_password_recovery(recovery_form)
  
@router.get("/permission/{permission_id}")
async def get_employees_with_permission(permission_id: int, search: str | None = None):
  return await handle_get_employees_with_permission(permission_id, search)

@router.get("/refresh-token")
async def refresh_token(employee_id: int):
  print(employee_id)
  return await handle_access_token_creation(employee_id)

@router.get("/permissions")
async def read_employee_permissions():
  return await handle_fetch_all_user_permissions()

@router.get("/requesters")
async def read_employee_requesters(company_id: int | None = None):
  return await handle_fetch_requester_employees(company_id)

@router.post("/authenticate-test")
async def authenticate_test(authentication_form: dict):
  return await handle_authentication_test(authentication_form)

@router.get("/existance/{employee_id}")
async def validate_employee_existance(employee_id: int):
  return await handle_validate_employee_existance(employee_id)

@router.get("/agents")
async def read_agents():
  return await handle_fetch_agents()

@router.get("/.current_user")
async def fetch_current_user(request: Request):
  return await handle_fetch_current_user(request)

@router.get("/.gateway_current_user")
async def fetch_current_user(request: Request):
  return await test_user_gateway(request)
  
@router.get("/_equipments")
async def read_equipment_users(request: Request, and_filters: str | None = None, order_by: str | None = None, ids_only: bool = False):
  print(and_filters, order_by, ids_only)
  return await handle_fetch_equipment_users(and_filters, order_by, ids_only)