from tortoise.models import Model
from tortoise import fields
from datetime import datetime
import hashlib
import os
import binascii

class Employees(Model):
  id = fields.IntField(pk=True)
  # Personal information
  first_name = fields.CharField(max_length=55)
  last_name = fields.CharField(max_length=55)
  full_name = fields.CharField(max_length=155, null=True)

  # Employee information
  employee_num = fields.CharField(max_length=15, null=True)
  extra_info = fields.TextField(null=True)
  created_at = fields.DatetimeField(auto_now_add=True)
  updated_at = fields.DatetimeField(auto_now_add=True)
  deactivated_at = fields.DatetimeField(null=True)
  deleted_at = fields.DatetimeField(null=True)
  
  # Login information
  username = fields.CharField(max_length=75, null=True)
  password = fields.CharField(max_length=155, null=True)
  recovery_token = fields.CharField(max_length=255, null=True)
  recovery_attempts = fields.IntField(default=4)
  last_time_seen = fields.DatetimeField(null=True)

  # Employee Foreign Keys
  department = fields.ForeignKeyField("helpdesk_models.Departments", related_name="department_relations", db_column="department_id")
  company = fields.ForeignKeyField("helpdesk_models.Companies", related_name="company_relations", db_column="company_id")
  local = fields.ForeignKeyField("helpdesk_models.Locals", related_name="local_relations", db_column="local_id")
  
  companies = fields.ManyToManyField(
    "helpdesk_models.Companies",
    related_name='employees',
    through='employees_companies',
    backward_key="employee_id",
    forward_key="company_id"
  )
  permissions = fields.ManyToManyField(
    "helpdesk_models.EmployeePermissions",
    related_name='employees_permissions',
    through='employee_employee_permissions',
    backward_key="employee_id",
    forward_key="employee_permission_id"
  )
  
  class Meta:
    table = "employees"
  
  async def to_dict_contacts(self) -> dict:
    department = await self.department
    company = await self.company
    local = await self.local
    public_contacts = [
      await contact.to_dict()
      for contact in await self.employee_relation.filter(public=True)
    ]
    return {
      "id": self.id,
      "first_name": self.first_name,
      "last_name": self.last_name,
      "full_name": self.full_name,
      "department": department.to_dict(),
      "company": company.to_dict(),
      "local": local.to_dict(),
      "contacts": public_contacts
    }
    
  async def to_dict(self) -> dict:
    department = await self.department
    company = await self.company
    local = await self.local
    public_contacts = [
      await contact.to_dict()
      for contact in await self.employee_relation.filter(main_contact=True)
    ]
    permissions = [permission.to_dict() for permission in await self.permissions.all()]
    return {
      "id": self.id,
      "first_name": self.first_name,
      "last_name": self.last_name,
      "full_name": self.full_name,
      "employee_num": self.employee_num,
      "deactivated_at": self.deactivated_at.strftime("%d/%m/%Y - %H:%M") if self.deactivated_at else None,
      "last_time_seen": self.last_time_seen.strftime("%d/%m/%Y - %H:%M") if self.last_time_seen else None,
      "department": department.to_dict(),
      "company": company.to_dict(),
      "local": local.to_dict(),
      "contacts": public_contacts,
      "permissions": permissions
    }
  
  async def to_dict_log(self) -> dict:
    companies = [company.name for company in await self.companies.all()]
    permissions = [permission.name for permission in await self.permissions.all()]
    department = await self.department,
    company = await self.company,
    local = await self.local,
    contacts = [await contact.to_dict_log() for contact in await self.employee_relation]
    return {
      "first_name": self.first_name,
      "last_name": self.last_name,
      "full_name": self.full_name,
      "username": self.username,
      "employee_num": self.employee_num,
      "extra_info": self.extra_info,
      "department": department[0].name,
      "company": company[0].name,
      "local": local[0].name,
      "companies": companies,
      "contacts": contacts,
      "permissions": permissions
    }
  
  async def to_dict_details(self) -> dict:
    companies = [company.to_dict() for company in await self.companies.all()]
    permissions = [permission.to_dict() for permission in await self.permissions.all()]
    department = await self.department
    company = await self.company
    local = await self.local
    contacts = [await contact.to_dict() for contact in await self.employee_relation]
    return {
      "id": self.id,
      "first_name": self.first_name,
      "last_name": self.last_name,
      "full_name": self.full_name,
      "username": self.username,
      "employee_num": self.employee_num,
      "extra_info": self.extra_info,
      "created_at": self.created_at.strftime("%d/%m/%Y - %H:%M"),
      "updated_at": self.updated_at.strftime("%d/%m/%Y - %H:%M"),
      "deactivated_at": self.deactivated_at.strftime("%d/%m/%Y - %H:%M") if self.deactivated_at else None,
      "last_time_seen": self.last_time_seen.strftime("%d/%m/%Y - %H:%M") if self.last_time_seen else None,
      "department": department.to_dict(),
      "company": company.to_dict(),
      "local": local.to_dict(),
      "companies": companies,
      "permissions": permissions,
      "contacts": contacts
    }
  
  def hash_password(password: str) -> str:
    # Generate a random salt
    salt = os.urandom(16)
    
    # Hash the password with the salt using PBKDF2
    key = hashlib.pbkdf2_hmac(
      'sha256',
      password.encode('utf-8'),
      salt,
      100000
    )
      
    return f"$pbkdf2-sha256$100000${binascii.hexlify(salt).decode()}${binascii.hexlify(key).decode()}"
  
  def verify_password(self, plain_password: str, stored_hash: str) -> bool:
    hash_encryption, iterations, salt_hex, key_hex = stored_hash.split('$')[1:]
    salt = binascii.unhexlify(salt_hex.encode())
    stored_key = binascii.unhexlify(key_hex.encode())
    
    new_key = hashlib.pbkdf2_hmac(
      hash_encryption.split("-")[1],
      plain_password.encode('utf-8'),
      salt,
      int(iterations)
    )
    
    return (new_key == stored_key)
  