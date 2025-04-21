from tortoise.models import Model
from tortoise import fields

class EmployeeContactTypes(Model):
  id = fields.IntField(pk=True)
  display_name = fields.CharField(max_length=35)
  name = fields.CharField(max_length=35)
  
  class Meta:
    table = "employee_contact_types"
  
  def to_dict(self):
    return {
      "id": self.id,
      "display_name": self.display_name,
      "name": self.name
    }