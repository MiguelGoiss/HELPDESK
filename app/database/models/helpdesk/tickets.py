from tortoise.models import Model
from tortoise import fields
from datetime import datetime
import hashlib
from tortoise.queryset import QuerySet
import pytz
lisbon_tz = pytz.timezone('Europe/Lisbon')

class Tickets(Model):
  id = fields.IntField(pk=True)
  uid = fields.CharField(max_length=80, null=True)
  subject = fields.CharField(max_length=255, null=True)
  request = fields.TextField()
  response = fields.TextField(null=True)
  internal_comment = fields.TextField(null=True)
  prevention_date = fields.DatetimeField(null=True)
  created_at = fields.DatetimeField()
  closed_at = fields.DatetimeField(null=True)
  spent_time = fields.IntField(default=15)
  supplier_reference = fields.CharField(max_length=255, null=True)

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
  
  ccs = fields.ManyToManyField(
    "helpdesk_models.Employees",
    related_name='employee_ccs',
    through='tickets_ccs',
    backward_key="ticket_id",
    forward_key="employee_id"
  )
  
  # TODO Retirar este comentário quando os equipamentos estiverem feitos
  # equipments = fields.ManyToManyField(
  #   "helpdesk_models.Tickets_Equipments",
  #   related_name='equipments',
  #   through='tickets_equipments',
  #   backward_key="ticket_id",
  #   forward_key="equipment_id"
  # )
  
  # TODO adicionar a many_to_many de fornecedores
  
  # TODO adicionar as fk de segurança
  
  # --- End Foreign Keys ---
  
  class Meta:
    table = "tickets"
  
  async def to_dict_log(self) -> dict[str, any]:
    try:
      company = await self.company
      category = await self.category
      subcategory = await self.subcategory
      status = await self.status
      type_ = await self.type
      priority = await self.priority
      assistance_type = await self.assistance_type
      created_by = await self.created_by
      requester = await self.requester
      agent = await self.agent
      ccs = [await cc.to_dict_employee_emails() for cc in await self.ccs.all()]
    except Exception as e:
      raise e
    
    return {
      "id": self.id,
      "uid": self.uid,
      "subject": self.subject,
      "request": self.request,
      "response": self.response,
      "internal_comment": self.internal_comment,
      "ccs": ccs,
      "prevention_date": self.prevention_date.isoformat() if self.prevention_date else None,
      "closed_at": self.closed_at.isoformat() if self.closed_at else None,
      "spent_time": self.spent_time,
      "supplier_reference": self.supplier_reference,
      "company": company.name if company else None,
      "category": category.name if category else None,
      "subcategory": subcategory.name if subcategory else None,
      "status": status.name if status else None,
      "type": type_.name if type_ else None,
      "priority": priority.name if priority else None,
      "assistance_type": assistance_type.name if assistance_type else None,
      "created_by": f"{created_by.first_name} {created_by.last_name}" if created_by else None,
      "requester": f"{requester.first_name} {requester.last_name}" if requester else None,
      "agent": f"{agent.first_name} {agent.last_name}" if agent else None,
    }
  
  async def to_dict(self):
    try:
      category = await self.category
      subcategory = await self.subcategory if self.subcategory else None
      status = await self.status
      priority = await self.priority
      requester = await self.requester
      agent = await self.agent if self.agent else None
      attachments = [attachment for attachment in await self.attachments.all()]
    except Exception as e:
      raise e
    
    return {
      "id": self.id,
      "uid": self.uid,
      "subject": self.subject,
      "request": self.request,
      "response": self.response,
      "closed_at": self.closed_at,
      "created_at": self.created_at,
      "status": status,
      "priority": priority,
      "category": category,
      "subcategory": subcategory,
      "requester": await requester.to_dict_contacts(),
      "agent": await agent.to_dict_contacts() if agent else None,
      "attachments": attachments
    }
  
  async def to_dict_details(self):
    try:
      category = await self.category
      subcategory = await self.subcategory if self.subcategory else None
      status = await self.status
      priority = await self.priority
      requester = await self.requester
      agent = await self.agent if self.agent else None
      attachments = [attachment for attachment in await self.attachments.all()]
      ccs = [await cc.to_dict_employee_emails() for cc in await self.ccs.all()]
      created_by = await self.created_by if self.created_by else None
      assistance_type = await self.assistance_type
      type_ = await self.type
      company = await self.company
    except Exception as e:
      raise e

    return {
      "id": self.id,
      "uid": self.uid,
      "subject": self.subject,
      "request": self.request,
      "response": self.response,
      "closed_at": self.closed_at.strftime("%d/%m/%Y - %H:%M") if self.closed_at else None,
      "created_at": self.created_at.strftime("%d/%m/%Y - %H:%M"),
      "prevention_date": self.prevention_date.astimezone(lisbon_tz).isoformat(),
      "status": status,
      "priority": priority,
      "category": category,
      "subcategory": subcategory,
      "requester": await requester.to_dict_contacts(),
      "agent": await agent.to_dict_contacts() if agent else None,
      "created_by":created_by,
      "assistance_type":assistance_type,
      "type":type_,
      "company":company,
      "attachments": attachments,
      "ccs":ccs,
      
    }
  
  async def _create_ticket(self, **kwargs):
    new_ticket = await Tickets.create(**kwargs)
    # Cria os detalhes para o hash
    try: 
      created_at_str = new_ticket.created_at.isoformat()
      data_to_hash = f"{new_ticket.id}-{created_at_str}-{new_ticket.requester_id}"
    except AttributeError:
      data_to_hash = f"{new_ticket.id}-{new_ticket.requester_id}-{datetime.now().isoformat()}"
    
    # Cria o uid
    hasher = hashlib.sha256()
    hasher.update(data_to_hash.encode('utf-8'))
    generated_uid = hasher.hexdigest()
    # Adiciona apenas o uid no novo ticket
    new_ticket.uid = generated_uid
    ticket_details = await new_ticket.to_dict_log()
    new_ticket.subject = f"[TICKET #{ticket_details['id']}] - {ticket_details['requester']} | {ticket_details['category']} | {ticket_details['priority']} | {new_ticket.created_at.strftime("%d/%m/%Y - %H:%M:%S")}"
    await new_ticket.save(update_fields=['uid', 'subject'])
    
    return new_ticket
  
  