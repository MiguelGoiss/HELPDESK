from pydantic import BaseModel, field_validator, ValidationInfo, Field
from app.utils.helpers.user_inputs import sanitize_input

class BaseCreateTicketCategory(BaseModel):
  name: str
  description: str | None = None
  companies: list[int] | None = None
  
  @field_validator('*', mode='before')
  def sanitize_fields(cls, value) -> any:
    return sanitize_input(value)
    
class BaseUpdateTicketCategory(BaseModel):
  name: str | None = None
  description: str | None = None
  active: bool = True
  companies: list[int] | None = None
  subcategories: list[str] | None = None
  
  @field_validator('*', mode='before')
  def sanitize_fields(cls, value, info: ValidationInfo) -> any:
    if info.field_name == "active":
      return value
    if isinstance(value, list):
      for item in value:
        sanitize_input(item, str(type(item)))
      return value
    return sanitize_input(value)
    

