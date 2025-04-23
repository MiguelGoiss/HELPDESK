from tortoise.models import Model
from tortoise import fields

class TicketCategories(Model):
  id = fields.IntField(pk=True)
  name = fields.CharField(max_length=35)
  description = fields.CharField(max_length=255, null=True)
  active = fields.BooleanField(default=True)
  
  class Meta:
    table = "ticket_categories"
  