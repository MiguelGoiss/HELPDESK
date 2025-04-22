from tortoise.models import Model
from tortoise import fields

class TicketPriorities(Model):
  id = fields.IntField(pk=True)
  name = fields.CharField(max_length=15)
  description = fields.CharField(max_length=255)
  color = fields.CharField(max_length=12)
  
  class Meta:
    table = "ticket_priorities"
  