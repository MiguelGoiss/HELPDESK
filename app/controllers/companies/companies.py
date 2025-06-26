from app.services.companies.companies import (
  create_company,
  fetch_companies,
  fetch_companies_management,
  fetch_company_by_id,
  update_company_details,
  deactivate_company,
)
from app.utils.errors.exceptions import CustomError
import logging
import json

logger = logging.getLogger(__name__)

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

async def handle_fetch_companies_management(
  path: str,
  page: int,
  page_size: int,
  original_query_params: dict,
  search: str | None,
  and_filters: str | None,
  order_by: str | None,
):
  try:
    logger.info(f"Handling fetch companies management request. Page: {page}, Page Size: {page_size}, Search: '{search}', Order By: '{order_by}'")
    parsed_and_filters = None
    if and_filters:
      try:
        parsed_and_filters = json.loads(and_filters)
        if not isinstance(parsed_and_filters, dict):
          raise ValueError("Parsed JSON is not a dictionary")
        logger.debug(f"Parsed and_filters: {parsed_and_filters}")
      except (json.JSONDecodeError, ValueError) as json_error:
        logger.error(f"Failed to parse and_filters JSON string: {and_filters}. Error: {json_error}", exc_info=True)
        raise CustomError(400, f"Invalid format for 'and_filters'. Expected a valid JSON object string. Error: {json_error}")

    result = await fetch_companies_management(
      path=path,
      page=page,
      page_size=page_size,
      original_query_params=original_query_params,
      search=search,
      and_filters=parsed_and_filters,
      order_by=order_by,
    )
    logger.info(f"Successfully fetched tickets. Page: {page}, Count: {len(result.get('items', []))}")
    return result

  except CustomError as e:
    logger.error(f"CustomError during fetching tickets: Status={e.status_code}, Detail={e.detail}", exc_info=True)
    raise e

  except Exception as e:
    logger.error(f"Unexpected error during fetching tickets: {e}", exc_info=True)
    raise e


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
    
