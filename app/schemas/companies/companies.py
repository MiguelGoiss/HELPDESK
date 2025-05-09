from pydantic import BaseModel, field_validator
from app.utils.helpers.client_inputs import sanitize_input

class LocalsSchema(BaseModel):
  name: str
  short: str
  background: str
  text: str
  
  @field_validator('*', mode="before")
  def sanitize_fields(cls, v):
    return sanitize_input(v)

class CompanyCreation(BaseModel):
  name: str
  acronym: str
  locals: list[LocalsSchema] | None = None
  ticket_category_ids: list[int] | None = None

  @field_validator('name', mode="before")
  def sanitize_fields(cls, v):
    return sanitize_input(v)
    
  @field_validator('acronym', mode="before")
  def sanitize_fields(cls, v):
    return sanitize_input(v)

class CompanyUpdate(BaseModel):
  name: str | None = None
  acronym: str | None = None
  locals: list[LocalsSchema] | None = None
  ticket_category_ids: list[int] | None = None

  @field_validator('name', mode="before")
  def sanitize_fields(cls, v):
    return sanitize_input(v)
    
  @field_validator('acronym', mode="before")
  def sanitize_fields(cls, v):
    return sanitize_input(v)