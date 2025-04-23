from tortoise.models import Model
from tortoise import fields

class Tickets_CCS(Model):
  id = fields.IntField(pk=True)
  ticket = fields.ForeignKeyField("helpdesk_models.Tickets", related_name="ccs_tickets_relation", db_column="ticket_id")
  employee = fields.ForeignKeyField("helpdesk_models.Employees", related_name="ccs_employees_relation", db_column="employee_id")
  
  class Meta:
    table = "tickets_ccs"
    unique_together = (("ticket", "employee"),)  # Prevent duplicate relationships