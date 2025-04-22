from tortoise.models import Model
from tortoise import fields

class TicketEquipments(Model):
  id = fields.IntField(pk=True)
  ticket = fields.ForeignKeyField(
    "helpdesk_models.Tickets",
    related_name="ticket_equipments",
    on_delete="CASCADE",
    db_column="ticket_id"
  )
  equipments = fields.JSONField()
  
  class Meta:
    table = "ticket_equipments"