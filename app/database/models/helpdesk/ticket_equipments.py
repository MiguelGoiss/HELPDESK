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
  # equipment = fields.ForeignKeyField(
  #   "equipments_models.Equipments",
  #   related_name="ticket_equipments",
  #   on_delete="CASCADE",
  #   db_column="equipment_id"
  # )
  
  class Meta:
    table = "ticket_equipments"