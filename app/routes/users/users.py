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
)
from app.schemas.users import UserCreate, UserResponse, UserUpdate, UserAuthentication, EmailForm, CodeForm, RecoveryForm
from app.utils.helpers.token import validate_access_token, validate_refresh_token
from app.services.users import require_permission 

router = APIRouter(prefix="/employees", tags=["Users"])

@router.post("", dependencies=[Depends(require_permission("tecnico"))], response_model=UserResponse)
async def create_user(user: UserCreate, current_user: dict = Depends(validate_access_token)):
  return await add_user(user, current_user)

@router.get("", dependencies=[Depends(require_permission("tecnico"))])
async def read_users(
  request: Request,
  page: int = Query(1, ge=1, description="Page number"),
  page_size: int = Query(10, ge=1, le=100, description="Items per page"),
  and_filters: str | None = None,
  order_by: str | None = None,
  search: str | None = None,
  _: dict = Depends(validate_access_token)
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

@router.get("/details/{id}", dependencies=[Depends(require_permission("tecnico"))])
async def get_user_details(id: int, _: dict = Depends(validate_access_token)):
  return await fetch_user_details(id)

@router.put("/details/{id}", dependencies=[Depends(require_permission("tecnico"))], description="Nos contactos apenas permite alterar o name, public e main_contact se for alterado o contact ou contact_type_id será eliminado e recriado com os novos dados.")
async def update_user_details(id:int, user_data: UserUpdate, current_user: dict = Depends(validate_access_token)):
  return await update_user(id, user_data, current_user)

@router.delete("/details/{id}", dependencies=[Depends(require_permission("tecnico"))])
async def delete_user_details(id: int, current_user: dict = Depends(validate_access_token)):
  return await delete_user(id, current_user)

@router.get("/me")#, dependencies=[Depends(require_permission("tickets"))])
async def read_user_me(current_user: dict = Depends(validate_access_token)):
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
async def get_employees_with_permission(permission_id: int):
  return await handle_get_employees_with_permission(permission_id)

@router.get("/refresh-token")
async def refresh_token(user_info: dict = Depends(validate_refresh_token)):
  return await handle_access_token_creation(user_info)

