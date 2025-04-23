from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# --- Carrega as variaveis do .env ---
# O load_dotenv é inicializado aqui porque vai ser necessário nos ficheiros abaixo
load_dotenv()
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
from app.routes.tickets import router as tickets_router

app.include_router(employees_router)
app.include_router(tickets_router)