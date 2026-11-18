from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "automation"
    app_env: str = "development"
    llm_provider: str = "mock"
    openai_api_key: str | None = None
    redis_url: str = "redis://localhost:6379/0"
    database_path: Path = Path("data/automation.db")
    chroma_path: Path = Path("chroma_data")
    slack_webhook_url: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

