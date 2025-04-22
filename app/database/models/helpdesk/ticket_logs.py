from tortoise.models import Model
from tortoise import fields

class TicketLogs(Model):
  id = fields.IntField(pk=True)
  action = fields.CharField(max_length=55)
  old_values = fields.JSONField()
  new_values = fields.JSONField()
  details = fields.CharField(max_length=55)
  created_at = fields.DatetimeField(auto_now_add=True)
  ticket = fields.ForeignKeyField(
    "helpdesk_models.Tickets",
    related_name="ticket_logs",
    db_column="ticket_id"
  )
  agent = fields.ForeignKeyField(
    "helpdesk_models.Employees",
    related_name="agent_logs",
    db_column="agent_id"
  )
  
  class Meta:
    table = "ticket_logs"
  