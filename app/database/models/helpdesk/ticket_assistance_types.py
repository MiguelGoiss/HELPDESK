from tortoise.models import Model
from tortoise import fields

class TicketAssistanceTypes(Model):
  id = fields.IntField(pk=True)
  name = fields.CharField(max_length=35)
  active = fields.BooleanField(default=True)
  
  class Meta:
    table = "ticket_assistance_types"
  