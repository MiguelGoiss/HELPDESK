import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path='.env.dev')

# encoded_password = quote_plus(os.getenv('DB_PASSWORD'))

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