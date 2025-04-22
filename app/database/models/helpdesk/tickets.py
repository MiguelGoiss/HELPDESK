from tortoise.models import Model
from tortoise import fields

class Tickets(Model):
  id = fields.IntField(pk=True)
  uid = fields.CharField(max_length=80, null=True)
  subject = fields.CharField(max_length=255, null=True)
  request = fields.TextField()
  response = fields.TextField(null=True)
  internal_comment = fields.TextField(null=True)
  ccs = fields.JSONField(null=True)
  prevention_date = fields.DatetimeField(null=True)
  created_at = fields.DatetimeField(auto_now_add=True)
  closed_at = fields.DatetimeField(null=True)
  spent_time = fields.IntField(default=15)
  supplier_reference = fields.CharField(max_length=255)

  # --- Foreign Keys --- 
  company = fields.ForeignKeyField(
    "helpdesk_models.Companies",
    related_name="company_tickets",
    db_column="company_id"
  )
  category = fields.ForeignKeyField(
    "helpdesk_models.TicketCategories",
    related_name="category_tickets",
    db_column="category_id"
  )
  subcategory = fields.ForeignKeyField(
    "helpdesk_models.TicketSubcategories",
    related_name="subcategory_tickets",
    db_column="subcategory_id",
    null=True
  )
  status = fields.ForeignKeyField(
    "helpdesk_models.TicketStatuses",
    related_name="status_tickets",
    db_column="status_id",
    default=1
  )
  type = fields.ForeignKeyField(
    "helpdesk_models.TicketTypes",
    related_name="type_tickets",
    db_column="type_id",
  )
  priority = fields.ForeignKeyField(
    "helpdesk_models.TicketPriorities",
    related_name="priority_tickets",
    db_column="priority_id",
    default=2
  )
  assistance_type = fields.ForeignKeyField(
    "helpdesk_models.TicketAssistanceTypes",
    related_name="assistance_type_tickets",
    db_column="assistance_type_id",
    default=2
  )
  created_by = fields.ForeignKeyField(
    "helpdesk_models.Employees",
    related_name="created_by_tickets",
    db_column="created_by_id",
    null=True
  )
  requester = fields.ForeignKeyField(
    "helpdesk_models.Employees",
    related_name="requester_tickets",
    db_column="requester_id"
  )
  agent = fields.ForeignKeyField(
    "helpdesk_models.Employees",
    related_name="agent_tickets",
    db_column="agent_id",
    null=True
  )
  
  # TODO adicionar as fk de segurança
  
  # --- End Foreign Keys ---
  
  class Meta:
    table = "tickets"
  
  def _create_ticket(self, **kwargs):
    print(**kwargs)
    return Tickets.create(**kwargs)