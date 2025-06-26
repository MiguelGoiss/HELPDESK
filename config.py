import os

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
    }
  },
  "apps": {
    "helpdesk_models": {
      "models": ["app.database.models.helpdesk"],
      "default_connection": "helpdesk",
    }
  }
}