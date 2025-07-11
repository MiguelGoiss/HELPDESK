from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.utils.errors.exceptions import CustomError
from dotenv import load_dotenv
import logging
from app.utils.logging.config import setup_logging
import asyncio
import httpx


setup_logging(log_level=logging.INFO)

# --- Carrega as variaveis do .env ---
# O load_dotenv é inicializado aqui porque vai ser necessário nos ficheiros abaixo
load_dotenv(dotenv_path='.env.dev')

# --- Variavéis do .env já estão carregadas  ---

from app.database.database import init_db, close_db, keep_connection_alive

@asynccontextmanager
async def lifespan(app: FastAPI):
  app.state.http_client = httpx.AsyncClient()
  await init_db()
  keepalive_task = asyncio.create_task(keep_connection_alive())
  try:
    yield
  finally:
    keepalive_task.cancel()
    try:
      await keepalive_task
    except asyncio.CancelledError:
      pass
    await close_db()
    await app.state.http_client.aclose()
  
    

app = FastAPI(title="IT Helpdesk | Tickets Service", lifespan=lifespan, version="1.0.0")

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

@app.middleware("http")
async def service_handshake_middleware(request:Request, call_next):
  # Import moved inside to avoid potential circular dependencies at startup
  from app.services.users.auth import _services_handshake 

  try:
    await _services_handshake(request)
    # Se o _services_handshake for executado com sucesso, continua para o próximo middleware/route
    response = await call_next(request)
    return response
  except CustomError as exc:
    logging.warning(f"Service handshake failed for {request.url.path}: {exc.detail.get('message')} - {exc.detail.get('info')}")

    return JSONResponse(
      status_code=exc.status_code,
      content=exc.detail 
    )
  except Exception as exc:
    # Handle any other unexpected errors during the handshake
    logging.error(f"Unexpected error during service handshake for {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
      status_code=500,
      content={"message": "Internal Server Error", "details": "An unexpected error occurred during service handshake."}
    )

from app.routes.users.users import router as employees_router
from app.routes.companies.companies import router as companies_router
from app.routes.departments.departments import router as departments_router
from app.routes.tickets import router as tickets_router
from app.routes.tickets.categories.ticket_categories import router as ticket_categories_router
from app.routes.tickets.subcategories.ticket_subcategories import router as ticket_subcategories_router
from app.routes.tickets.assistance_types.ticket_assistance_types import router as ticket_assistance_types_router
from app.routes.tickets.types.ticket_types import router as ticket_types_router
from app.routes.tickets.priorities.ticket_priorities import router as ticket_priorities_router
from app.routes.tickets.status import ticket_status_router

app.include_router(employees_router, prefix="/api/v1")
app.include_router(companies_router, prefix="/api/v1")
app.include_router(departments_router, prefix="/api/v1")
app.include_router(tickets_router, prefix="/api/v1")
app.include_router(ticket_categories_router, prefix="/api/v1")
app.include_router(ticket_subcategories_router, prefix="/api/v1")
app.include_router(ticket_assistance_types_router, prefix="/api/v1")
app.include_router(ticket_types_router, prefix="/api/v1")
app.include_router(ticket_priorities_router, prefix="/api/v1")
app.include_router(ticket_status_router, prefix="/api/v1")