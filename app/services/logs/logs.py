# from fastapi import Request
from tortoise.models import Model

class LogService:
  async def log_action(
    # request: Request,
    action_type: str,
    employee_id: int,
    model: Model,
    target_id: int | None = None,
    old_values: dict[str, any] | None = None,
    new_values: dict[str, any] | None = None,
    details: str | None = None
  ) -> None:
    # ip_address = request.client.host if request.client else None
    # user_agent = request.headers.get("user-agent")
    
    await model.create(
      action_type=action_type,
      employee_id=employee_id,
      target_id=target_id,
      old_values=old_values,
      new_values=new_values,
      details=details,
      # ip_address=ip_address,
      # user_agent=user_agent
    )