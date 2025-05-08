from fastapi import Form, HTTPException
from pydantic import BaseModel, EmailStr, field_validator, ValidationInfo
from datetime import datetime
from app.utils.helpers.client_inputs import sanitize_input
import json

class BaseSupplierContacts(BaseModel):
  contact_id: int

class BaseTicketSuppliers(BaseModel):
  supplier_id: int
  contacts: list[BaseSupplierContacts] | None = None

class BaseEquipments(BaseModel):
  equipment_id: int

class BaseCreateTicket(BaseModel):
  company_id: int
  requester_id: int
  category_id: int
  type_id: int
  request: str
  subcategory_id: int | None = None
  assistance_type_id: int | None = None
  response: str | None = None
  internal_comment: str | None = None
  suppliers: list[BaseTicketSuppliers] | None = None
  equipments: list[BaseEquipments] | None = None
  prevention_date: datetime | None = None
  spent_time: int | None = None
  status_id: int | None = None
  agent_id: int | None = None
  supplier_reference: str | None = None
  ccs: list[int] | None = None
  
  @field_validator('*', mode='before')
  def sanitize_fields(cls, v, info: ValidationInfo):
    field_name = info.field_name
    if isinstance(v, str):
      if field_name not in ['suppliers', 'equipments', 'ccs']:
        return sanitize_input(v, allow_special_chars=True) if v is not None else None
    return v

  @classmethod
  def as_form(
    cls,
    company_id: int = Form(...),
    requester_id: int = Form(...),
    category_id: int = Form(...),
    type_id: int = Form(...),
    request: str = Form(...),
    subcategory_id: int | None = Form(None),
    assistance_type_id: int | None = Form(None),
    response: str | None = Form(None),
    internal_comment: str | None = Form(None),
    suppliers: str | None = Form(None),
    equipments: str | None = Form(None),
    prevention_date: datetime | None = Form(None),
    spent_time: int | None = Form(None),
    status_id: int | None = Form(None),
    agent_id: int | None = Form(None),  
    supplier_reference: str | None = Form(None),
    ccs: str | None = Form(None)
  ):
    parsed_suppliers = None
    if suppliers:
      try:
        suppliers_list = json.loads(suppliers)
        parsed_suppliers = suppliers_list
      except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for suppliers field.")
      except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing suppliers: {e}")

    parsed_equipments = None
    if equipments:
      try:
        equipments_list = json.loads(equipments)
        parsed_equipments = equipments_list
      except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for equipments field.")
      except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing equipments: {e}")

    parsed_ccs: list[int] | None = None
    if ccs:
      if ccs.strip():
        try:
          parsed_ccs = [int(item.strip()) for item in ccs.split(',') if item.strip()]
          if not parsed_ccs:
            parsed_ccs = None
        except ValueError:
          raise HTTPException(
            status_code=422,
            detail=[{
              "loc": ["body", "ccs"],
              "msg": "Input should be a comma-separated string of valid integers",
              "type": "value_error.integerparsing",
              "input": ccs
            }]
          )
        except Exception as e:
          raise HTTPException(status_code=400, detail=f"Error processing ccs: {e}")
      else:
        # If the input string was empty or just whitespace, treat as None
        parsed_ccs = None

    return cls(
      company_id=company_id,
      requester_id=requester_id,
      category_id=category_id,
      type_id=type_id,
      request=request,
      subcategory_id=subcategory_id,
      assistance_type_id=assistance_type_id,
      response=response,
      internal_comment=internal_comment,
      suppliers=parsed_suppliers,
      equipments=parsed_equipments,
      prevention_date=prevention_date,
      spent_time=spent_time,
      status_id=status_id,
      agent_id=agent_id,
      supplier_reference=supplier_reference,
      ccs=parsed_ccs
    )

class BaseUpdateTicket(BaseModel):
  requester_id: int | None = None
  category_id: int | None = None
  type_id: int | None = None
  subcategory_id: int | None = None
  assistance_type_id: int | None = None
  response: str | None = None
  internal_comment: str | None = None
  suppliers: list[BaseTicketSuppliers] | None = None
  equipments: list[BaseEquipments] | None = None
  prevention_date: datetime | None = None
  spent_time: int | None = None
  status_id: int | None = None
  agent_id: int | None = None
  supplier_reference: str | None = None
  ccs: list[int] | None = None
  
  @field_validator('*', mode='before')
  def sanitize_fields(cls, v, info: ValidationInfo):
    field_name = info.field_name
    if isinstance(v, str):
      if field_name not in ['suppliers', 'equipments', 'ccs']:
        return sanitize_input(v, allow_special_chars=True) if v is not None else None
    return v

  @classmethod
  def as_form(
    cls,
    requester_id: int | None = Form(None),
    category_id: int | None = Form(None),
    type_id: int | None = Form(None),
    subcategory_id: int | None = Form(None),
    assistance_type_id: int | None = Form(None),
    response: str | None = Form(None),
    internal_comment: str | None = Form(None),
    suppliers: str | None = Form(None),
    equipments: str | None = Form(None),
    prevention_date: datetime | None = Form(None),
    spent_time: int | None = Form(None),
    status_id: int | None = Form(None),
    agent_id: int | None = Form(None),
    supplier_reference: str | None = Form(None),
    ccs: str | None = Form(None)
  ):
    parsed_suppliers = None
    if suppliers:
      try:
        suppliers_list = json.loads(suppliers)
        parsed_suppliers = suppliers_list
      except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for suppliers field.")
      except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing suppliers: {e}")

    parsed_equipments = None
    if equipments:
      try:
        equipments_list = json.loads(equipments)
        parsed_equipments = equipments_list
      except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for equipments field.")
      except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing equipments: {e}")

    parsed_ccs: list[int] | None = None
    if ccs:
      if ccs.strip():
        try:
          parsed_ccs = [int(item.strip()) for item in ccs.split(',') if item.strip()]
          if not parsed_ccs:
            parsed_ccs = None
        except ValueError:
          raise HTTPException(
            status_code=422,
            detail=[{
              "loc": ["body", "ccs"],
              "msg": "Input should be a comma-separated string of valid integers",
              "type": "value_error.integerparsing",
              "input": ccs
            }]
          )
        except Exception as e:
          raise HTTPException(status_code=400, detail=f"Error processing ccs: {e}")
    else:
      # If the input string was empty or just whitespace, treat as None
      parsed_ccs = []

    return cls(
      requester_id=requester_id,
      category_id=category_id,
      type_id=type_id,
      subcategory_id=subcategory_id,
      assistance_type_id=assistance_type_id,
      response=response,
      internal_comment=internal_comment,
      suppliers=parsed_suppliers,
      equipments=parsed_equipments,
      prevention_date=prevention_date,
      spent_time=spent_time,
      status_id=status_id,
      agent_id=agent_id,
      supplier_reference=supplier_reference,
      ccs=parsed_ccs
    )
    