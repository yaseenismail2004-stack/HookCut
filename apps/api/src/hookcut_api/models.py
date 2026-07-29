from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Float, Integer, String, Text, func
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
