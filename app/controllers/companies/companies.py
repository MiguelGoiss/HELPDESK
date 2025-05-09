from app.services.companies.companies import (
  create_company,
  fetch_companies,
  fetch_company_by_id,
  update_company_details,
  deactivate_company,
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

async def handle_create_company(company_data: dict):
  try:
    return await create_company(company_data)
  except CustomError as e:
    raise e
  except Exception as e:
    raise CustomError(
      500,
      "Ocorreu um erro ao criar a empresa.",
      str(e)
    ) from e

async def handle_fetch_company_by_id(company_id: int):
  try:
    return await fetch_company_by_id(company_id)
  except CustomError as e:
    raise e
  except Exception as e:
    raise CustomError(
      500,
      f"Ocorreu um erro ao obter a empresa com ID {company_id}.",
      str(e)
    ) from e

async def handle_update_company_details(company_id: int, company_data: dict):
  try:
    return await update_company_details(company_id, company_data)
  except CustomError as e:
    raise e
  except Exception as e:
    raise CustomError(
      500,
      f"Ocorreu um erro ao atualizar a empresa com ID {company_id}.",
      str(e)
    ) from e

async def handle_deactivate_company(company_id: int):
  try:
    await deactivate_company(company_id)
    return {"message": f"Empresa com ID {company_id} desativada com sucesso."}
  except CustomError as e:
    raise e
  except Exception as e:
    raise CustomError(
      500,
      f"Ocorreu um erro ao desativar a empresa com ID {company_id}.",
      str(e)
    ) from e
    
