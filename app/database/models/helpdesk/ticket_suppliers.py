from tortoise.models import Model
from tortoise import fields

class TicketSuppliers(Model):
  id = fields.IntField(pk=True)
  ticket = fields.ForeignKeyField(
    "helpdesk_models.Tickets",
    related_name="ticket_suppliers",
    on_delete="CASCADE",
    db_column="ticket_id"
  )
  contacts = fields.JSONField()
  
  class Meta:
    table = "ticket_suppliers"