from tortoise.models import Model
from tortoise import fields

class TicketTypes(Model):
  id = fields.IntField(pk=True)
  name = fields.CharField(max_length=20)
  description = fields.CharField(max_length=255)
  color = fields.CharField(max_length=12)
  
  class Meta:
    table = "ticket_types"

  def to_dict(self) -> dict:
    """Serializa a instancia de TicketTypes para um dicionário."""
    return {
      "id": self.id,
      "name": self.name,
      "description": self.description,
      "color": self.color
    }
  