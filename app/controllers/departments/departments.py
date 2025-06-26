from app.services.departments.departments import (
  create_department,
  fetch_departments,
  fetch_departments_management,
  fetch_department_by_id,
  update_department_details,
  deactivate_department,
)
from app.utils.errors.exceptions import CustomError
from app.schemas.departments import DepartmentCreation, DepartmentsUpdate
import logging
import json

logger = logging.getLogger(__name__)

async def handle_create_department(department_data: DepartmentCreation):
  try:
    return await create_department(department_data)

  except CustomError as e:
    raise e

  except Exception as e:
    raise CustomError(
      500,
      "Ocorreu um erro ao criar o departamento.",
      str(e)
    ) from e

async def handle_fetch_departments():
  try:
    return await fetch_departments()

  except CustomError as e:
    raise e

  except Exception as e:
    raise CustomError(
      500,
      "Ocorreu um erro ao obter os departamentos.",
      str(e)
    ) from e

async def handle_fetch_departments_management(
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

    result = await fetch_departments_management(
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

async def handle_fetch_department_by_id(department_id: int):
  try:
    return await fetch_department_by_id(department_id)

  except CustomError as e:
    raise e

  except Exception as e:
    raise CustomError(
      500,
      f"Ocorreu um erro ao obter o departamento com ID {department_id}.",
      str(e)
    ) from e

async def handle_update_department_details(department_id: int, department_data: DepartmentsUpdate):
  try:
    return await update_department_details(department_id, department_data)

  except CustomError as e:
    raise e

  except Exception as e:
    raise CustomError(
      500,
      f"Ocorreu um erro ao atualizar o departamento com ID {department_id}.",
      str(e)
    ) from e

async def handle_deactivate_department(department_id: int):
  try:
    await deactivate_department(department_id)
    return {"message": f"Departamento com ID {department_id} desativado com sucesso."}

  except CustomError as e:
    raise e

  except Exception as e:
    raise CustomError(
        500,
        f"Ocorreu um erro ao desativar o departamento com ID {department_id}.",
        str(e)
    ) from e