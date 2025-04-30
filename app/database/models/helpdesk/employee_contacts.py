from tortoise.models import Model
from tortoise import fields

class EmployeeContacts(Model):
  id = fields.IntField(pk=True)
  contact = fields.CharField(max_length=255)
  name = fields.CharField(max_length=55)
  main_contact = fields.BooleanField(default=False)
  public = fields.BooleanField(default=True)
  contact_type = fields.ForeignKeyField(model_name="helpdesk_models.EmployeeContactTypes", related_name="contact_type_relation", db_column="contact_type_id")
  employee = fields.ForeignKeyField(model_name="helpdesk_models.Employees", related_name="employee_relation", db_column="employee_id")
   
  class Meta:
    table = "employee_contacts"

  def _contact(self):
    return self.contact

  async def to_dict_log(self):
    contact_type = await self.contact_type
    return {
      "contact_type": contact_type.name,
      "name": self.name,
      "main_contact": self.main_contact,
      "public": self.public
    }
  
  async def to_dict(self):
    contact_type_obj = await self.contact_type
    contact_type = contact_type_obj.to_dict() if contact_type_obj else None
    return {
      "id": self.id,
      "contact_type": contact_type,
      "contact": self.contact,
      "name": self.name,
      "main_contact": self.main_contact,
    }
  