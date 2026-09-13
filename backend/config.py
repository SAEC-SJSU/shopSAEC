import os
from pathlib import Path

from pydantic_settings import BaseSettings

_root = Path(__file__).resolve().parent.parent
_env_file = str(_root / ".env.dev") if os.getenv("ENV", "dev") == "dev" else str(_root / ".env.local")


class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "shop_saec"
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "SAEC Shop <orders@we-saec.me>"
    FRONTEND_URL: str = "http://localhost:3000"
    MANAGER_PASSWORD: str = ""
    # Optional: dedicated signing secret for manager sessions. When blank the
    # key is derived from MANAGER_PASSWORD instead.
    MANAGER_SECRET: str = ""
    MANAGER_SESSION_HOURS: int = 8

    model_config = {
        "env_file": _env_file,
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
