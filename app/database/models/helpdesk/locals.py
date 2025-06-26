from tortoise.models import Model
from tortoise import fields

class Locals(Model):
  id = fields.IntField(pk=True)
  name = fields.CharField(max_length=50)
  short = fields.CharField(max_length=10)
  background = fields.CharField(max_length=10, null=True)
  text = fields.CharField(max_length=10, null=True)
  
  company = fields.ForeignKeyField(
    "helpdesk_models.Companies",
    related_name="company_local_relations",
    db_column="company_id"
  )

  class Meta:
    table = "locals"
  
  def to_dict(self):
    return {
      "id": self.id,
      "name": self.name,
      "short": self.short,
      "background": self.background,
      "text": self.text,
    }
    