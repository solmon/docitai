import os


APP_ENV = os.getenv("APP_ENV", "development").lower()
OPEN_API_ENABLED = os.getenv("__OPEN_API__", "false").lower() == "true"
