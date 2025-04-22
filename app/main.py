from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routes.users.users import router as user_router
from app.database.database import init_db, close_db
from fastapi.middleware.cors import CORSMiddleware

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

app.include_router(user_router)