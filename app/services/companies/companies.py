import logging
from app.database.models.helpdesk import Companies
from app.utils.errors.exceptions import CustomError

logger = logging.getLogger(__name__)

async def fetch_companies() -> list[dict]:
  """
  Obtém todas as empresas ativas.

  Returns:
    Uma lista de dicionários, onde cada dicionário representa uma empresa.

  Raises:
    CustomError: Se ocorrer algum erro durante a busca dos dados.
  """
  try:
    # Filtra empresas que não estão desativadas (deactivated_at é Nulo)
    # e ordena pelo nome.
    companies_orm = await Companies.filter(deactivated_at__isnull=True).order_by('name').all()
    return [company.to_dict() for company in companies_orm]

  except Exception as e:
    logger.error(f"Unexpected error fetching companies: {e}", exc_info=True)
    raise CustomError(
      500,
      "Ocorreu um erro ao obter as empresas.",
      str(e)
    ) from e