from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


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
    gemini_api_key_configured: bool
    gemini_sdk_available: bool = False
    gemini_transcription_model_configured: bool = False
    gemini_transcription_provider_available: bool = False
    openai_api_key_configured: bool
    openai_sdk_available: bool = False
    transcription_model_configured: bool = False
    transcription_provider_available: bool = False
    configured_transcription_providers: list[str] = Field(default_factory=list)
    primary_transcription_provider: str = "gemini"
    cost_estimation_configured: bool = False
    database_configured: bool


class CapabilitiesResponse(BaseModel):
    python: ToolAvailability
    ffmpeg: ToolAvailability
    ffprobe: ToolAvailability
    storage: StorageCapabilities
    configuration: ConfigurationState
    worker_running: bool = False


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


class TranscriptionJobRequest(BaseModel):
    language_mode: str = "auto"
    provider: str = "gemini"
    approve_estimated_cost: bool = False


class JobResponse(BaseModel):
    id: str
    video_id: str
    state: str
    current_stage: str
    progress_percent: float | None
    progress_indeterminate: bool
    estimated_cost_usd: float | None
    cost_approval_required: bool
    retry_available: bool
    cancellation_available: bool
    error_code: str | None
    error_key: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class TranscriptPartResponse(BaseModel):
    index: int
    start_seconds: float
    end_seconds: float
    text: str
    confidence: float | None


class TranscriptResponse(BaseModel):
    id: str
    video_id: str
    provider: str
    model: str
    detected_language: str | None
    language_confidence: float | None
    full_text: str
    duration_seconds: float
    status: str
    segments: list[TranscriptPartResponse]
    words: list[TranscriptPartResponse]


class ClipSelectionJobRequest(BaseModel):
    requested_clip_count: int = Field(ge=1, le=10)
    platform: str
    duration_mode: str = "auto"
    selection_mode: str = "balanced"
    diversity_mode: str = "strict"
    approve_estimated_cost: bool = False


class ClipSelectionRunResponse(BaseModel):
    id: str
    video_id: str
    transcript_id: str
    job_id: str
    requested_clip_count: int
    platform: str
    duration_mode: str
    selection_mode: str
    diversity_mode: str
    provider: str
    model: str | None
    estimated_cost_usd: float | None
    candidate_count: int
    selected_count: int
    reserve_count: int
    rejected_count: int
    status: str
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class ClipCandidateResponse(BaseModel):
    id: str
    selection_run_id: str
    start_seconds: float
    end_seconds: float
    duration_seconds: float
    timestamp_precision: str
    transcript_text: str
    topic: str
    summary: str
    hook_type: str
    hook_text: str
    hook_score: float
    first_1_second_score: float
    first_3_seconds_score: float
    first_5_seconds_score: float
    retention_score: float
    retention_reason: str
    viral_potential_score: float
    confidence_score: float
    ideal_platform: str
    suggested_title: str
    suggested_on_screen_hook: str
    detected_weaknesses: list[str]
    boundary_mode: str
    selection_status: str
    selection_reason: str
    rejection_reason: str | None
    similarity_group: str | None


class ManualSelectionRequest(BaseModel):
    selection_status: str
