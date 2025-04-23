from tortoise.models import Model
from tortoise import fields

class TicketAttachments(Model):
  id = fields.IntField(pk=True)
  filename = fields.CharField(max_length=355)
  original_name = fields.CharField(max_length=255)
  extension = fields.CharField(max_length=15)
  created_at = fields.DatetimeField(auto_now_add=True)
  ticket = fields.ForeignKeyField(
    "helpdesk_models.Tickets",
    related_name="attachments",
    db_column="ticket_id"
  )
  agent = fields.ForeignKeyField(
    "helpdesk_models.Employees",
    related_name="uploaded_attachments",
    db_column="agent_id"
  )
  
  class Meta:
    table = "ticket_attachments"
  