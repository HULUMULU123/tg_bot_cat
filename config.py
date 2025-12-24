from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
import os


@dataclass
class Settings:
    bot_token: str
    api_secret: str
    db_path: str


def load_settings(env_file: str | None = None) -> Settings:
    """Load settings from .env file and environment variables."""
    env_path = Path(env_file) if env_file else Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()

    bot_token = os.getenv("BOT_TOKEN")
    api_secret = os.getenv("API_SECRET")
    db_path = os.getenv("DB_PATH") or str(Path(__file__).parent / "data.sqlite3")

    if not bot_token:
        raise ValueError("BOT_TOKEN is required. Set it in the .env file or environment variables.")
    if not api_secret:
        raise ValueError("API_SECRET is required. Set it in the .env file or environment variables.")

    return Settings(bot_token=bot_token, api_secret=api_secret, db_path=db_path)
