from tortoise import Tortoise
from tortoise.transactions import in_transaction
from config import DATABASE_CONFIG
from app.database.models.helpdesk import Companies
import asyncio

async def init_db():
  await Tortoise.init(config=DATABASE_CONFIG)
  # await Tortoise.generate_schemas(safe=True)

async def close_db():
  await Tortoise.close_connections()
    

async def keep_connection_alive():
  while True:
    try:
      async with in_transaction():
        await Companies.exists()
    except Exception:
      pass
    await asyncio.sleep(60 * 40)  # ping every 40 mins