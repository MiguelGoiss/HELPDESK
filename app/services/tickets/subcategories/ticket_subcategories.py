import logging
from app.database.models.helpdesk import TicketSubcategories
from app.utils.errors.exceptions import CustomError

logger = logging.getLogger(__name__)

async def delete_ticket_subcategory(subcategory_id: int) -> None:
  """
  Deleta uma subcategoria de ticket pelo seu ID.

  Args:
    subcategory_id: O ID da subcategoria a ser eliminada.

  Raises:
    CustomError: Se a subcategoria não for encontrada ou se ocorrer um erro durante a deleção.
  """
  try:
    subcategory_to_delete = await TicketSubcategories.get_or_none(id=subcategory_id)
    if not subcategory_to_delete:
      raise CustomError(
        404, 
        "Subcategoria de ticket não encontrada", 
        f"Nenhuma subcategoria encontrada com o ID: {subcategory_id}"
      )

    await subcategory_to_delete.delete()
    logger.info(f"Subcategoria de ticket com ID {subcategory_id} eliminada com sucesso.")

  except CustomError as e:
    raise e
  except Exception as e:
    logger.error(f"Erro inesperado ao deletar subcategoria de ticket com ID {subcategory_id}: {e}", exc_info=True)
    raise CustomError(
      500,
      "Ocorreu um erro ao deletar a subcategoria de ticket.",
      str(e)
    ) from e