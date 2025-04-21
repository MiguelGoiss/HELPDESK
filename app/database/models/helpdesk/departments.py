from tortoise.models import Model
from tortoise import fields

class Departments(Model):
  id = fields.IntField(pk=True)
  name = fields.CharField(max_length=75)

  class Meta:
    table = "departments"
  
  def to_dict(self):
    return {
      "id": self.id,
      "name": self.name
    }
  