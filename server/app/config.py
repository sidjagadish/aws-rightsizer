import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    app_env: str = os.getenv("APP_ENV", "dev")
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/rightsizer"
    )

settings = Settings()
