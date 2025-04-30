from tortoise.models import Model
from tortoise import fields

class TicketPresets(Model):
  id = fields.IntField(pk=True)
  name = fields.CharField(max_length=20)
  description = fields.CharField(max_length=255, null=True)
  color = fields.CharField(max_length=12)
  
  class Meta:
    table = "ticket_presets"
  
  def __str__(self):
    return self.name
  
  def to_dict(self):
    return {
      "id": self.id,
      "name": self.name,
      "description": self.description,
      "color": self.color
    }