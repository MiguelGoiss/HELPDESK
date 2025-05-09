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
  
  async def to_dict_related(self):
    company_locals = await self.company_local_relations.all()
    return {
      "id": self.id,
      "name": self.name,
      "acronym": self.acronym,
      "locals": [local.to_dict() for local in company_locals]
    }
  
  async def to_dict_details(self):
    """
    Serializa os detalhes de uma empresa com os locais e categorias de ticket associadas.
    """
    company_locals_orm = await self.company_local_relations.all()
    company_ticket_category_relations = await self.company_ticket_categories.all().prefetch_related('ticket_category')
    
    ticket_categories_list = []
    for relation in company_ticket_category_relations:
      category = relation.ticket_category 
      ticket_categories_list.append(category.id)
      
    return {
      "id": self.id,
      "name": self.name,
      "acronym": self.acronym,
      "deactivated_at": self.deactivated_at.isoformat() if self.deactivated_at else None,
      "locals": [local.to_dict() for local in company_locals_orm],
      "ticket_categories": ticket_categories_list
    }
    