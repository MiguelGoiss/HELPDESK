from app.database.models.helpdesk import TicketCategories, TicketSubcategories
from app.utils.errors.exceptions import CustomError

async def _validate_category_name(category_name: str, category_id: int | None = None):
  """
  Valida se o nome da categoria já existe na base de dados.

  Args:
    category_name: O nome da categoria a ser validado.
    category_id: O id da categoria a ser ignorada na verificação (para updates).

  Raises:
    CustomError: Se o nome da categoria já existir ou ocorrer algum erro durante a busca.
  """
  try:
    if category_id:
      existing_category = await TicketCategories.get_or_none(name=category_name, active=True).exclude(id=category_id)
    else:
      existing_category = await TicketCategories.get_or_none(name=category_name, active=True)
    if not existing_category:
      return True
    
    raise CustomError(
      409,
      "Uma categoria com o nome inserido já existe",
      f"Uma categoria com o nome: {category_name} já existe criado com o id: {existing_category.id}"
    )
  except Exception as e:
    raise CustomError(
      500,
      "Ocorreu um erro ao validar o nome da categoria inserido",
      str(e)
    )
  