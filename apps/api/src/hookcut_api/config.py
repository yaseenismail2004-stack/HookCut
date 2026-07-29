from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, PositiveFloat, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    """Runtime configuration. Values are read from environment variables only."""

    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    app_version: str = "0.1.0"
    storage_root: str = "storage"
    web_origin: str = "http://127.0.0.1:3000"
    api_host: str = "127.0.0.1"
    api_port: PositiveInt = 8000
    max_upload_size_mb: PositiveInt = 4096
    max_video_duration_seconds: PositiveInt = 7200
    max_ai_cost_per_video_hour_usd: PositiveFloat = 1.5
    openai_api_key: str | None = None
    database_url: str | None = None

    @property
    def resolved_storage_root(self) -> Path:
        candidate = Path(self.storage_root)
        if not candidate.is_absolute():
            candidate = PROJECT_ROOT / candidate
        return candidate.resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
