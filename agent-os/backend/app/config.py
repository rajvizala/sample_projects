from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "AgentOS"
    debug: bool = False

    database_url: str = "sqlite+aiosqlite:///./agentOS.db"
    redis_url: str = "redis://localhost:6379"
    redis_ttl: int = 3600

    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
