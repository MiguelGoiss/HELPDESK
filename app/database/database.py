from tortoise import Tortoise
from config import DATABASE_CONFIG

async def init_db():
    await Tortoise.init(config=DATABASE_CONFIG)
    await Tortoise.generate_schemas(safe=True)

async def close_db():
    await Tortoise.close_connections()