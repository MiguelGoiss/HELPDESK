from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routes.users.users import router as user_router
from app.database.database import init_db, close_db

@asynccontextmanager
async def lifespan(app: FastAPI):
  await init_db()
  yield
  await close_db()

app = FastAPI(lifespan=lifespan)

app.include_router(user_router)