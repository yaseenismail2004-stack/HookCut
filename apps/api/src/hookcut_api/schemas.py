from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ToolAvailability(BaseModel):
    available: bool
    version: str | None = None


class StorageCapabilities(BaseModel):
    directories_ready: bool
    project_write_permission: bool


class ConfigurationState(BaseModel):
    openai_api_key_configured: bool
    database_configured: bool


class CapabilitiesResponse(BaseModel):
    python: ToolAvailability
    ffmpeg: ToolAvailability
    ffprobe: ToolAvailability
    storage: StorageCapabilities
    configuration: ConfigurationState
