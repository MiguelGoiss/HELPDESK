from tortoise.models import Model
from tortoise import fields

class Tickets_Equipments(Model):
  id = fields.IntField(pk=True)
  ticket = fields.ForeignKeyField("helpdesk_models.Tickets", related_name="ticket_relations", db_column="ticket_id")
  equipment = fields.ForeignKeyField("equipments_models.Equipments", related_name="equipment_relations", db_column="equipment_id")
  
  class Meta:
    table = "tickets_equipments"
    unique_together = (("ticket", "equipment"),)  # Prevent duplicate relationships