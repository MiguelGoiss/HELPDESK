from tortoise.models import Model
from tortoise import fields

class EmployeeLogs(Model):
  id = fields.IntField(pk=True)
  action_type = fields.CharField(max_length=50)
  agent = fields.ForeignKeyField("helpdesk_models.Employees", related_name="agent_log", db_column="agent_id") 
  target = fields.ForeignKeyField("helpdesk_models.Employees", related_name="employee_log", db_column="target_id", null=True)
  old_values = fields.JSONField(null=True)
  new_values = fields.JSONField(null=True)
  details = fields.TextField(null=True)
  ip_address = fields.CharField(max_length=50, null=True)
  user_agent = fields.CharField(max_length=255, null=True)
  created_at = fields.DatetimeField(auto_now_add=True)

  class Meta:
    table = "employee_logs"
  
  