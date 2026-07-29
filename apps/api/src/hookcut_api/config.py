from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import NonNegativeFloat, PositiveFloat, PositiveInt, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    """Runtime configuration. Values are read from environment variables only."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_version: str = "0.1.0"
    storage_root: str = "storage"
    web_origin: str = "http://127.0.0.1:3000"
    api_host: str = "127.0.0.1"
    api_port: PositiveInt = 8000
    max_upload_size_mb: PositiveInt = 4096
    max_video_duration_seconds: PositiveInt = 7200
    max_ai_cost_per_video_hour_usd: PositiveFloat = 1.5
    openai_api_key: str | None = None
    openai_transcription_model: str | None = None
    openai_transcription_cost_per_minute_usd: NonNegativeFloat | None = None
    openai_request_timeout_seconds: PositiveInt = 120
    gemini_api_key: str | None = None
    gemini_transcription_model: str = "gemini-3.6-flash"
    gemini_transcription_cost_per_minute_usd: NonNegativeFloat | None = None
    gemini_request_timeout_seconds: PositiveInt = 120
    worker_poll_interval_seconds: PositiveFloat = 0.5
    worker_enabled: bool = True
    database_url: str = "sqlite:///storage/hookcut.db"

    @field_validator(
        "openai_api_key",
        "openai_transcription_model",
        "openai_transcription_cost_per_minute_usd",
        "gemini_api_key",
        "gemini_transcription_cost_per_minute_usd",
        mode="before",
    )
    @classmethod
    def empty_optional_values_are_unset(cls, value: object) -> object:
        """Allow template placeholders to remain empty until configured locally."""
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("database_url", mode="before")
    @classmethod
    def empty_database_url_uses_local_default(cls, value: object) -> object:
        """Keep the checked-in template usable without a local override."""
        if isinstance(value, str) and not value.strip():
            return "sqlite:///storage/hookcut.db"
        return value

    @property
    def resolved_storage_root(self) -> Path:
        candidate = Path(self.storage_root)
        if not candidate.is_absolute():
            candidate = PROJECT_ROOT / candidate
        return candidate.resolve()

    @property
    def resolved_database_url(self) -> str:
        prefix = "sqlite:///"
        if not self.database_url.startswith(prefix) or self.database_url.startswith("sqlite:////"):
            return self.database_url
        database_path = Path(self.database_url.removeprefix(prefix))
        if database_path.is_absolute():
            return self.database_url
        return f"{prefix}{(PROJECT_ROOT / database_path).resolve().as_posix()}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
