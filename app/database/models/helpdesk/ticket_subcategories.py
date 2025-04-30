from tortoise.models import Model
from tortoise import fields

class TicketSubcategories(Model):
  id = fields.IntField(pk=True)
  name = fields.CharField(max_length=35)
  active = fields.BooleanField(default=True)
  category = fields.ForeignKeyField(
    model_name="helpdesk_models.TicketCategories",
    related_name="category_subcategories",
    db_column="category_id"
  )
  
  class Meta:
    table = "ticket_subcategories"
  
  def to_dict(self):
    return {
      "id": self.id,
      "name": self.name
    }
  