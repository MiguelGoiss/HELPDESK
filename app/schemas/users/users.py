from pydantic import BaseModel, EmailStr, field_validator, ValidationInfo
from app.utils.helpers.user_inputs import sanitize_input

class EmployeeContacts(BaseModel):
  contact: str
  name: str
  main_contact: bool | None = None
  public: bool | None = None
  contact_type_id: int

class UserCreate(BaseModel):
  first_name: str 
  last_name: str
  full_name: str | None = None
  username: str | None = None
  password: str | None = None
  employee_num: str | None = None
  extra_info: str | None = None
  department_id: int
  company_id: int
  local_id: int
  companies: list[int] | None = None
  contacts: list[EmployeeContacts] | None = None
  permissions: list[int] | None = None
  
  @field_validator('*')
  def validate_username(cls, v:str, info: ValidationInfo) -> str:
    if info.field_name == 'password':
      if len(v) < 9:
        raise ValueError('Password must be at least 9 characters long')
      return v
    elif info.field_name.endswith("_id"):
      return sanitize_input(v, "int")
    elif info.field_name in ['companies', 'contacts', 'permissions']:
      return v
    return sanitize_input(v, allow_special_chars=True)

class UserUpdate(BaseModel):
  first_name: str | None = None
  last_name: str | None = None
  full_name: str | None = None
  username: str | None = None
  password: str | None = None
  employee_num: str | None = None
  extra_info: str | None = None
  deactivate: bool | None = None
  contacts: list[EmployeeContacts] | None = None
  companies: list[int] | None = None
  permissions: list[int] | None = None
  department_id: int | None = None
  company_id: int | None = None
  local_id: int | None = None
  
  @field_validator('*')
  def validate_username(cls, v:str, info: ValidationInfo) -> str:
    if info.field_name == 'deactivate' and isinstance(v, bool):
      return v
    if info.field_name == 'password':
      if len(v) < 9:
        raise ValueError('Password must be at least 9 characters long')
      return v
    elif info.field_name.endswith("_id"):
      return sanitize_input(v, "int")
    elif info.field_name in ['companies', 'contacts', 'permissions']:
      return v
    return sanitize_input(v, allow_special_chars=True)
  
class UserResponse(UserCreate):
  id: int

class UserResponse(BaseModel):
  id: int
  first_name: str
  last_name: str
  full_name: str
  username: str
  email: str

class UserAuthentication(BaseModel):
  username: str
  password: str
  
  @field_validator('username')
  def validate_username(cls, v:str) -> str:
    return sanitize_input(v, allow_special_chars=True)

class EmailForm(BaseModel):
  email: EmailStr | None = None

class CodeForm(BaseModel):
  code: str
  id: int
  @field_validator('code')
  def validate_username(cls, v:str) -> str:
    return sanitize_input(v)


class RecoveryForm(CodeForm):
  password: str
  
  @field_validator('password')
  def validate_password(cls, v:str) -> str:
    if len(v) < 9:
      raise ValueError('Password must be at least 9 characters long')
    return v