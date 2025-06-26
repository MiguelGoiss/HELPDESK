from pydantic import BaseModel

class ServiceAuthentication(BaseModel):
  service_name: str
  service_audience: str