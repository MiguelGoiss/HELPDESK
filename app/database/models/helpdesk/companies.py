from tortoise.models import Model
from tortoise import fields

class Companies(Model):
  id = fields.IntField(pk=True)
  name = fields.CharField(max_length=55, null=True)
  acronym = fields.CharField(max_length=7)
  deactivated_at = fields.DatetimeField(null=True)

  departments = fields.ManyToManyField(
    "helpdesk_models.Departments",
    related_name="companies",
    through="companies_departments",
    forward_key="department_id", # Field in Companies_Departments pointing to Departments
    backward_key="company_id"    # Field in Companies_Departments pointing to Companies
  )
  
  class Meta:
    table = "companies"

  def to_dict(self):
    return {
      "id": self.id,
      "name": self.name,
      "acronym": self.acronym
    }

  async def to_dict_pagination(self):
    company_departments = await self.departments.all() # Fetch related departments
    return {
      "id": self.id,
      "name": self.name,
      "acronym": self.acronym,
      "departments": [department.to_dict() for department in company_departments] # Serialize departments
    }
  
  async def to_dict_related(self):
    company_locals = await self.company_local_relations.all()
    company_departments = await self.departments.all() # Fetch related departments
    return {
      "id": self.id,
      "name": self.name,
      "acronym": self.acronym,
      "locals": [local.to_dict() for local in company_locals],
      "departments": [department.to_dict() for department in company_departments] # Serialize departments
    }
  
  async def to_dict_details(self):
    """
    Serializa os detalhes de uma empresa com os locais e categorias de ticket associadas.
    """
    company_locals_orm = await self.company_local_relations.all()
    company_ticket_category_relations = await self.ticket_categories.all()
    ticket_categories_list = [category.to_dict_companies() for category in company_ticket_category_relations]
    
    return {
      "id": self.id,
      "name": self.name,
      "acronym": self.acronym,
      "deactivated_at": self.deactivated_at.isoformat() if self.deactivated_at else None,
      "locals": [local.to_dict() for local in company_locals_orm],
      "ticket_categories": ticket_categories_list
    }
    