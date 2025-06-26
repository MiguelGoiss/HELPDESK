from tortoise.models import Model
from tortoise import fields

class Departments(Model):
  id = fields.IntField(pk=True)
  name = fields.CharField(max_length=255, unique=True)
  deactivated_at = fields.DatetimeField(null=True)

  class Meta:
    table = "departments"

  def to_dict(self):
    return {
      "id": self.id,
      "name": self.name
    }
    
  async def to_dict_pagination(self):
    return {
      "id": self.id,
      "name": self.name
    }
    
  def to_dict_with_companies(self):
    companies_list = [company.to_dict() for company in self.companies]
    return {
      "id": self.id,
      "name": self.name,
      "companies": companies_list,
    }