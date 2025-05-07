from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging
from app.utils.logging.config import setup_logging 

setup_logging(log_level=logging.INFO)

# --- Carrega as variaveis do .env ---
# O load_dotenv é inicializado aqui porque vai ser necessário nos ficheiros abaixo
load_dotenv(dotenv_path='.env.dev')

# --- Variavéis do .env já estão carregadas  ---

from app.database.database import init_db, close_db

@asynccontextmanager
async def lifespan(app: FastAPI):
  await init_db()
  yield
  await close_db()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

from app.routes.users.users import router as employees_router
from app.routes.companies.companies import router as companies_router
from app.routes.tickets import router as tickets_router
from app.routes.tickets.categories.ticket_categories import router as ticket_categories_router
from app.routes.tickets.subcategories.ticket_subcategories import router as ticket_subcategories_router
from app.routes.tickets.assistance_types.ticket_assistance_types import router as ticket_assistance_types_router
from app.routes.tickets.types.ticket_types import router as ticket_types_router
from app.routes.tickets.priorities.ticket_priorities import router as ticket_priorities_router

app.include_router(employees_router, prefix="/api/v1")
app.include_router(companies_router, prefix="/api/v1")
app.include_router(tickets_router, prefix="/api/v1")
app.include_router(ticket_categories_router, prefix="/api/v1")
app.include_router(ticket_subcategories_router, prefix="/api/v1")
app.include_router(ticket_assistance_types_router, prefix="/api/v1")
app.include_router(ticket_types_router, prefix="/api/v1")
app.include_router(ticket_priorities_router, prefix="/api/v1")