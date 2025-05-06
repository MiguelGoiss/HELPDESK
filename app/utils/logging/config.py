import logging
import sys

# --- ANSI Color Codes ---
RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
BOLD_RED = "\033[1;31m"

class ColorFormatter(logging.Formatter):
  """Logging formatter customizado que adiciona cores com base no nível de log."""

  LEVEL_COLORS = {
    logging.DEBUG: CYAN,
    logging.INFO: GREEN,
    logging.WARNING: YELLOW,
    logging.ERROR: RED,
    logging.CRITICAL: BOLD_RED,
  }

  def __init__(self, fmt="%(levelname)s:%(name)s:%(message)s", datefmt=None, style='%', use_colors=True):
    super().__init__(fmt=fmt, datefmt=datefmt, style=style)
    self.use_colors = use_colors

  def format(self, record):
    """Formata o log adicionando a cor."""
    # Obtem a mensagem na formatação original
    log_message = super().format(record)

    if self.use_colors:
      # Obtem a cor para o log
      color = self.LEVEL_COLORS.get(record.levelno, RESET)
      # Adiciona a cor no início e reset no fim
      return f"{color}{log_message}{RESET}"
    else:
      return log_message

def setup_logging(log_level: int = logging.INFO, use_colors: bool = True):
  logger = logging.getLogger()
  logger.setLevel(log_level)

  console_handler = logging.StreamHandler(sys.stderr) 
  console_handler.setLevel(log_level) # Processa mensagens deste nivel para cima

  # Cria e adiciona o formato
  log_format = '%(asctime)s - %(name)s -> %(levelname)s \n\t\t %(message)s'
  date_format = '%Y-%m-%d %H:%M:%S'

  formatter = ColorFormatter(fmt=log_format, datefmt=date_format, use_colors=use_colors)
  console_handler.setFormatter(formatter)
  
  if logger.hasHandlers():
    logger.handlers.clear()

  logger.addHandler(console_handler)

  logging.info("Logging configured successfully.")

