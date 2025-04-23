from tortoise.models import Model
from tortoise import fields

class TicketSupplierContacts(Model):
  id = fields.IntField(pk=True)
  ticket_supplier = fields.ForeignKeyField(
    "helpdesk_models.TicketSuppliers",
    related_name="ticket_supplier_contacts",
    on_delete="CASCADE",
    db_column="ticket_supplier_id"
  )
  # supplier_contact = fields.ForeignKeyField(
  #   "equipments_models.SupplierContacts",
  #   related_name="ticket_supplier_contacts",
  #   on_delete="CASCADE",
  #   db_column="supplier_contact_id"
  # )
  
  class Meta:
    table = "ticket_supplier_contacts"