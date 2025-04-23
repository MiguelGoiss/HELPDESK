from tortoise.models import Model
from tortoise import fields

class TicketLogs(Model):
  id = fields.IntField(pk=True)
  action_type = fields.CharField(max_length=55)
  old_values = fields.JSONField(null=True)
  new_values = fields.JSONField(null=True)
  details = fields.TextField(null=True)
  created_at = fields.DatetimeField(auto_now_add=True)
  target = fields.ForeignKeyField(
    "helpdesk_models.Tickets",
    related_name="ticket_logs",
    db_column="target_id"
  )
  agent = fields.ForeignKeyField(
    "helpdesk_models.Employees",
    related_name="agent_logs",
    db_column="agent_id"
  )
  
  class Meta:
    table = "ticket_logs"
  