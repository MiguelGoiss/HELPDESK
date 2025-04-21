from tortoise.models import Model
from tortoise import fields

class EmployeesCompanies(Model):
  id = fields.IntField(pk=True)
  employee = fields.ForeignKeyField("helpdesk_models.Employees", related_name="employee_relations", db_column="employee_id")
  company = fields.ForeignKeyField("helpdesk_models.Companies", related_name="company_user_relations", db_column="company_id")
  
  class Meta:
    table = "employees_companies"
    unique_together = (("employee", "company"),)  # Prevent duplicate relationships