from fastapi import HTTPException

class CustomError(HTTPException):
  def __init__(self, status_code: int, message: str, info: str | None = None):
    super().__init__(
      status_code, 
      {
        "message": message, 
        "info": info
      }
    )