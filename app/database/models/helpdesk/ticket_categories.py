from tortoise.models import Model
from tortoise import fields

class TicketCategories(Model):
  id = fields.IntField(pk=True)
  name = fields.CharField(max_length=35)
  description = fields.CharField(max_length=255, null=True)
  active = fields.BooleanField(default=True)
  
  companies = fields.ManyToManyField(
    "helpdesk_models.Companies",
    related_name="ticket_categories",
    through="ticket_categories_companies",
    backward_key="ticket_category_id",
    forward_key="company_id"
  )
  
  class Meta:
    table = "ticket_categories"
  
  async def to_dict(self) -> dict:
    """
    Serializa o TicketCategory para um dicionário,
    incluindo associações com empresas e subcategorias ativas. 
    """
    related_companies = await self.companies.all()
    related_subcategories = await self.category_subcategories.filter(active=True).all()

    return {
      "id": self.id,
      "name": self.name,
      "description": self.description,
      "active": self.active,
      "companies": [{"id": company.id, "name": company.name} for company in related_companies],
      "subcategories": [sub.to_dict() for sub in related_subcategories]
    }