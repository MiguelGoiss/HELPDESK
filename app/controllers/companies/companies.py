from app.services.companies.companies import (
  fetch_companies,
)
from app.utils.errors.exceptions import CustomError

async def handle_fetch_companies():
  try:
    return await fetch_companies()

  except CustomError as e:
    raise e

  except Exception as e:
    raise CustomError(
      500,
      "Ocorreu um erro a obter as empresas.",
      str(e)
    ) from e