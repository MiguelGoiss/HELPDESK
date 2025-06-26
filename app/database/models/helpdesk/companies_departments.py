from tortoise.models import Model
from tortoise import fields

class Companies_Departments(Model):
  id = fields.IntField(pk=True)
  company = fields.ForeignKeyField("helpdesk_models.Companies", related_name="company_user_relations", db_column="company_id")
  department = fields.ForeignKeyField("helpdesk_models.Departments", related_name="department_relations", db_column="department_id")
  
  class Meta:
    table = "companies_departments"
    unique_together = (("company", "department"),)  # Previne relações duplicadas