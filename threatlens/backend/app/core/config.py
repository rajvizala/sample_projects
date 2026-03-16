from pydantic_settings import BaseSettings
from pathlib import Path
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "ThreatLens"
    app_version: str = "1.0.0"
    debug: bool = False

    database_url: str = "sqlite:///./threatlens.db"
    secret_key: str = "change-me-in-production"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    gemini_api_key: str = ""
    ml_models_dir: str = str(Path(__file__).parent.parent / "ml" / "trained_models")
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
