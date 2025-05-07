from tortoise.models import Model
from tortoise import fields

class TicketPriorities(Model):
  id = fields.IntField(pk=True)
  name = fields.CharField(max_length=35)
  description = fields.CharField(max_length=255)
  level = fields.IntField(unique=True) # Defines the order of priority, e.g., 1 (highest) to 5 (lowest)
  color = fields.CharField(max_length=12, null=True) # e.g., hex color code
  
  class Meta:
    table = "ticket_priorities"

  def to_dict(self) -> dict:
    """Serializa a instancia TicketPriorities para um dicionário."""
    return {
      "id": self.id,
      "name": self.name,
      "description": self.description,
      "level": self.level,
      "color": self.color,
    }