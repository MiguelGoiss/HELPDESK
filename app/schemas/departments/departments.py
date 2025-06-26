from pydantic import BaseModel, field_validator
from app.utils.helpers.client_inputs import sanitize_input

class DepartmentCreation(BaseModel):
  name: str
  company_ids: list[int] | None = None
  
  @field_validator('name')
  def sanitize_fields(cls, v):
    return sanitize_input(v)
    
class DepartmentsUpdate(BaseModel):
  name: str | None = None
  company_ids: list[int] | None = None

  @field_validator('name')
  def sanitize_fields(cls, v):
    return sanitize_input(v)