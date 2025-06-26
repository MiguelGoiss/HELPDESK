from tortoise.models import Model
from tortoise import fields

class TicketStatuses(Model):
  id = fields.IntField(pk=True)
  name = fields.CharField(max_length=25)
  color = fields.CharField(max_length=12)
  text_color = fields.CharField(max_length=12)
  
  class Meta:
    table = "ticket_statuses"
  
  def to_dict(self):
    return {
      "id": self.id,
      "name": self.name,
      "color": self.color,
      "text_color": self.text_color,
    }
  