from tortoise.models import Model
from tortoise import fields

class EmployeePermissions(Model):
  id = fields.IntField(pk=True)
  name = fields.CharField(max_length=50)
  display_name = fields.CharField(max_length=50)
  description = fields.CharField(max_length=555)
  
  class Meta:
    table = "employee_permissions"
  
  def to_dict(self):
    return {
      "id": self.id,
      "name": self.name,
      "display_name": self.display_name,
      "description": self.description
    }
  
  