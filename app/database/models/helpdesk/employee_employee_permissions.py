from tortoise.models import Model
from tortoise import fields

class Employee_EmployeePermissions(Model):
  id = fields.IntField(pk=True)
  employee = fields.ForeignKeyField("helpdesk_models.Employees", related_name="employee_permissions_relation", db_column="employee_id")
  employee_permission = fields.ForeignKeyField("helpdesk_models.EmployeePermissions", related_name="permissions_relation", db_column="employee_permission_id")
  
  class Meta:
    table = "employee_employee_permissions"
    unique_together = (("employee", "employee_permission"),)  # Prevent duplicate relationships
    
  
  