from __future__ import annotations

from datetime import datetime

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


class VideoResponse(BaseModel):
    id: str
    original_filename: str
    file_size_bytes: int
    container: str | None
    duration_seconds: float | None
    width: int | None
    height: int | None
    frame_rate: float | None
    video_codec: str | None
    audio_codec: str | None
    audio_channels: int | None
    audio_sample_rate: int | None
    status: str
    validation_error: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DeleteVideoResponse(BaseModel):
    id: str
    status: str
    already_deleted: bool


class ErrorDetail(BaseModel):
    code: str
    message: str
