from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from hookcut_api.db import Base


class VideoStatus(StrEnum):
    UPLOADING = "uploading"
    VALIDATING = "validating"
    READY = "ready"
    REJECTED = "rejected"
    DELETED = "deleted"


class VideoAsset(Base):
    __tablename__ = "video_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    container: Mapped[str | None] = mapped_column(String(64))
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    frame_rate: Mapped[float | None] = mapped_column(Float)
    video_codec: Mapped[str | None] = mapped_column(String(64))
    audio_codec: Mapped[str | None] = mapped_column(String(64))
    audio_channels: Mapped[int | None] = mapped_column(Integer)
    audio_sample_rate: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[VideoStatus] = mapped_column(String(16), nullable=False)
    validation_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class JobType(StrEnum):
    TRANSCRIPTION = "transcription"


class JobState(StrEnum):
    QUEUED = "queued"
    VALIDATING_SOURCE = "validating_source"
    EXTRACTING_AUDIO = "extracting_audio"
    AUDIO_READY = "audio_ready"
    ESTIMATING_COST = "estimating_cost"
    AWAITING_COST_APPROVAL = "awaiting_cost_approval"
    TRANSCRIBING = "transcribing"
    SAVING_TRANSCRIPT = "saving_transcript"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AudioArtifactStatus(StrEnum):
    EXTRACTING = "extracting"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


class TranscriptStatus(StrEnum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("video_assets.id"), nullable=False, index=True)
    job_type: Mapped[JobType] = mapped_column(String(32), nullable=False)
    state: Mapped[JobState] = mapped_column(String(32), nullable=False, index=True)
    progress_percent: Mapped[float | None] = mapped_column(Float)
    current_stage: Mapped[str] = mapped_column(String(64), nullable=False)
    language_mode: Mapped[str] = mapped_column(String(8), nullable=False)
    transcription_provider: Mapped[str] = mapped_column(String(32), nullable=False)
    transcription_model: Mapped[str | None] = mapped_column(String(128))
    estimated_cost_usd: Mapped[float | None] = mapped_column(Float)
    actual_cost_usd: Mapped[float | None] = mapped_column(Float)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    cancellation_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cost_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(String(512))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class AudioArtifact(Base):
    __tablename__ = "audio_artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("video_assets.id"), nullable=False, index=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("processing_jobs.id"), nullable=False, index=True)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    codec: Mapped[str | None] = mapped_column(String(64))
    sample_rate: Mapped[int | None] = mapped_column(Integer)
    channels: Mapped[int | None] = mapped_column(Integer)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[AudioArtifactStatus] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("video_assets.id"), nullable=False, index=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("processing_jobs.id"), nullable=False, unique=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    detected_language: Mapped[str | None] = mapped_column(String(32))
    language_confidence: Mapped[float | None] = mapped_column(Float)
    full_text: Mapped[str] = mapped_column(Text, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[TranscriptStatus] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    transcript_id: Mapped[str] = mapped_column(ForeignKey("transcripts.id"), nullable=False, index=True)
    segment_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    end_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)


class TranscriptWord(Base):
    __tablename__ = "transcript_words"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    transcript_id: Mapped[str] = mapped_column(ForeignKey("transcripts.id"), nullable=False, index=True)
    segment_id: Mapped[str | None] = mapped_column(ForeignKey("transcript_segments.id"))
    word_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    end_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    text: Mapped[str] = mapped_column(String(512), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
