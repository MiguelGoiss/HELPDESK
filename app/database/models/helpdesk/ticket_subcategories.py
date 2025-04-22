from tortoise.models import Model
from tortoise import fields

class TicketSubcategories(Model):
  id = fields.IntField(pk=True)
  name = fields.CharField(max_length=15)
  category = fields.ForeignKeyField(
    model_name="helpdesk_models.TicketCategories",
    related_name="category_subcategories",
    db_column="category_id"
  )
  
  class Meta:
    table = "ticket_subcategories"
  