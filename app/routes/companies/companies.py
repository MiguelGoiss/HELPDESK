from fastapi import APIRouter
from app.controllers.companies.companies import (
  handle_fetch_companies,
)

router = APIRouter(prefix="/companies", tags=["Companies"])

@router.get("")
async def fetch_companies():
  try:
    return await handle_fetch_companies()
  except Exception as e:
    raise e