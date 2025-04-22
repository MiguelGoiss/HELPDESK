from tortoise.models import Model
from tortoise import fields

class TicketCategories_Companies(Model):
  id = fields.IntField(pk=True)
  ticket_category = fields.ForeignKeyField(
    "helpdesk_models.TicketCategories",
    related_name="ticket_category_companies",
    db_column="ticket_category_id"
  )
  company = fields.ForeignKeyField(
    "helpdesk_models.Companies",
    related_name="company_ticket_categories",
    db_column="company_id"
  )
  
  class Meta:
    table = "ticket_categories_companies"
    unique_together = (("ticket_category", "company"),)  # Prevent duplicate relationships
    
  