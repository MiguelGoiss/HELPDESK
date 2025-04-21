from tortoise.models import Model
from tortoise import fields

class Companies(Model):
  id = fields.IntField(pk=True)
  name = fields.CharField(max_length=55, null=True)
  acronym = fields.CharField(max_length=7)
  deactivated_at = fields.DatetimeField(null=True)
  
  class Meta:
    table = "companies"

  def to_dict(self):
    return {
      "id": self.id,
      "name": self.name,
      "acronym": self.acronym
    }
    