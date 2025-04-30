import os
from urllib.parse import quote_plus

DATABASE_CONFIG = {
  "connections": {
    "helpdesk": {
      "engine": "tortoise.backends.mysql",
      "credentials": {
        "host": os.getenv('HELPDESKDB_HOST'),
        "port": os.getenv('HELPDESKDB_PORT'),
        "user": os.getenv('HELPDESKDB_USER'),
        "password": os.getenv('HELPDESKDB_PASSWORD'),
        "database": os.getenv('HELPDESKDB_NAME'),
        "minsize": 1,
        "maxsize": 10,
        "connect_timeout": 30, # segundos
      }
    },
    "equipments": {
      "engine": "tortoise.backends.mysql",
      "credentials": {
        "host": os.getenv('ATIVOSDB_HOST'),
        "port": os.getenv('ATIVOSDB_PORT'),
        "user": os.getenv('ATIVOSDB_USER'),
        "password": os.getenv('ATIVOSDB_PASSWORD'),
        "database": os.getenv('ATIVOSDB_NAME'),
        "minsize": 1,
        "maxsize": 10,
        "connect_timeout": 30, # segundos
      }
    }
  },
  "apps": {
    "helpdesk_models": {
      "models": ["app.database.models.helpdesk"],
      "default_connection": "helpdesk",
    },
    "equipments_models": {
      "models": ["app.database.models.equipments"],
      "default_connection": "equipments",
    }
  }
}