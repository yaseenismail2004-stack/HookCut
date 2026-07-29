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
    CLIP_SELECTION = "clip_selection"


class JobState(StrEnum):
    QUEUED = "queued"
    VALIDATING_SOURCE = "validating_source"
    EXTRACTING_AUDIO = "extracting_audio"
    AUDIO_READY = "audio_ready"
    ESTIMATING_COST = "estimating_cost"
    AWAITING_COST_APPROVAL = "awaiting_cost_approval"
    TRANSCRIBING = "transcribing"
    SAVING_TRANSCRIPT = "saving_transcript"
    LOADING_TRANSCRIPT = "loading_transcript"
    GENERATING_CANDIDATES = "generating_candidates"
    OPTIMIZING_BOUNDARIES = "optimizing_boundaries"
    ANALYZING_CANDIDATES = "analyzing_candidates"
    SCORING_HOOKS = "scoring_hooks"
    ESTIMATING_RETENTION = "estimating_retention"
    DEDUPLICATING = "deduplicating"
    SELECTING_FINAL_SET = "selecting_final_set"
    SAVING_RESULTS = "saving_results"
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


class ClipSelectionRun(Base):
    __tablename__ = "clip_selection_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("video_assets.id"), nullable=False, index=True)
    transcript_id: Mapped[str] = mapped_column(ForeignKey("transcripts.id"), nullable=False, index=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("processing_jobs.id"), nullable=False, unique=True)
    requested_clip_count: Mapped[int] = mapped_column(Integer, nullable=False)
    platform: Mapped[str] = mapped_column(String(16), nullable=False)
    duration_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    minimum_duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    maximum_duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    selection_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    diversity_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="strict")
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str | None] = mapped_column(String(128))
    estimated_cost_usd: Mapped[float | None] = mapped_column(Float)
    actual_cost_usd: Mapped[float | None] = mapped_column(Float)
    candidate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    selected_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reserve_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejected_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ClipCandidate(Base):
    __tablename__ = "clip_candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    selection_run_id: Mapped[str] = mapped_column(ForeignKey("clip_selection_runs.id"), nullable=False, index=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("video_assets.id"), nullable=False, index=True)
    transcript_id: Mapped[str] = mapped_column(ForeignKey("transcripts.id"), nullable=False, index=True)
    start_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    end_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp_precision: Mapped[str] = mapped_column(String(16), nullable=False, default="segment")
    transcript_text: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str] = mapped_column(String(256), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    hook_type: Mapped[str] = mapped_column(String(64), nullable=False)
    hook_text: Mapped[str] = mapped_column(Text, nullable=False)
    hook_score: Mapped[float] = mapped_column(Float, nullable=False)
    hook_reason: Mapped[str] = mapped_column(Text, nullable=False)
    first_1_second_score: Mapped[float] = mapped_column(Float, nullable=False)
    first_3_seconds_score: Mapped[float] = mapped_column(Float, nullable=False)
    first_5_seconds_score: Mapped[float] = mapped_column(Float, nullable=False)
    retention_score: Mapped[float] = mapped_column(Float, nullable=False)
    retention_reason: Mapped[str] = mapped_column(Text, nullable=False)
    standalone_score: Mapped[float] = mapped_column(Float, nullable=False)
    usefulness_score: Mapped[float] = mapped_column(Float, nullable=False)
    entertainment_score: Mapped[float] = mapped_column(Float, nullable=False)
    emotional_impact_score: Mapped[float] = mapped_column(Float, nullable=False)
    share_potential_score: Mapped[float] = mapped_column(Float, nullable=False)
    save_potential_score: Mapped[float] = mapped_column(Float, nullable=False)
    comment_potential_score: Mapped[float] = mapped_column(Float, nullable=False)
    loop_potential_score: Mapped[float] = mapped_column(Float, nullable=False)
    visual_suitability_score: Mapped[float] = mapped_column(Float, nullable=False)
    viral_potential_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    ideal_platform: Mapped[str] = mapped_column(String(16), nullable=False)
    target_audience: Mapped[str] = mapped_column(String(256), nullable=False)
    likely_viewer_reaction: Mapped[str] = mapped_column(String(256), nullable=False)
    suggested_title: Mapped[str] = mapped_column(String(256), nullable=False)
    suggested_on_screen_hook: Mapped[str] = mapped_column(String(256), nullable=False)
    detected_weaknesses: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    boundary_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="balanced_segment")
    selection_status: Mapped[str] = mapped_column(String(32), nullable=False, default="candidate")
    selection_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    similarity_group: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
