from __future__ import annotations

import logging
from pathlib import Path
from collections.abc import Generator
from typing import cast
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from hookcut_api.config import Settings
from hookcut_api.models import VideoAsset, VideoStatus
from hookcut_api.schemas import DeleteVideoResponse, VideoResponse
from hookcut_api.services.media_validation import MediaValidationError, SUPPORTED_EXTENSIONS, probe_and_validate
from hookcut_api.services.storage import StorageService


router = APIRouter(prefix="/api/videos", tags=["videos"])
CHUNK_SIZE = 1024 * 1024
logger = logging.getLogger(__name__)


def _error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def _safe_original_filename(filename: str | None) -> str:
    name = Path(filename or "video").name.strip().replace("\x00", "")
    return name[:255] or "video"


def _commit(session: Session, phase: str) -> None:
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        logger.exception("event=database_save_failed phase=%s", phase)
        raise
    logger.info("event=database_save_completed phase=%s", phase)


def get_db(request: Request) -> Generator[Session, None, None]:
    session: Session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


def get_storage(request: Request) -> StorageService:
    return cast(StorageService, request.app.state.storage)


def get_settings_from_app(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


@router.post("/upload", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    request: Request,
    file: UploadFile = File(...),
    session: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage),
    settings: Settings = Depends(get_settings_from_app),
) -> VideoResponse:
    original_filename = _safe_original_filename(file.filename)
    extension = Path(original_filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS or not (file.content_type or "").startswith("video/"):
        raise _error(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "unsupported_format", "Upload MP4, MOV, MKV, or WebM video media.")
    stored_filename, destination = storage.new_upload_path(extension)
    asset = VideoAsset(id=str(uuid4()), original_filename=original_filename, stored_filename=stored_filename, file_size_bytes=0, status=VideoStatus.UPLOADING)
    written = 0
    try:
        session.add(asset)
        _commit(session, "upload_record_created")
        with destination.open("xb") as output:
            while chunk := await file.read(CHUNK_SIZE):
                if await request.is_disconnected():
                    raise MediaValidationError("upload_cancelled", "Upload was cancelled.")
                written += len(chunk)
                if written > settings.max_upload_size_mb * 1024 * 1024:
                    raise MediaValidationError("file_too_large", "File exceeds the maximum permitted upload size.")
                output.write(chunk)
        asset.file_size_bytes = written
        asset.status = VideoStatus.VALIDATING
        _commit(session, "upload_body_completed")
        logger.info("event=upload_body_completed asset_id=%s bytes=%s", asset.id, written)
        logger.info("event=validation_started asset_id=%s", asset.id)
        metadata = probe_and_validate(destination, extension, settings.max_video_duration_seconds)
        asset.container = metadata.container
        asset.duration_seconds = metadata.duration_seconds
        asset.width = metadata.width
        asset.height = metadata.height
        asset.frame_rate = metadata.frame_rate
        asset.video_codec = metadata.video_codec
        asset.audio_codec = metadata.audio_codec
        asset.audio_channels = metadata.audio_channels
        asset.audio_sample_rate = metadata.audio_sample_rate
        asset.status = VideoStatus.READY
        _commit(session, "validation_completed")
        session.refresh(asset)
        response = VideoResponse.model_validate(asset)
        logger.info("event=response_returned asset_id=%s status=ready", asset.id)
        return response
    except MediaValidationError as error:
        asset.status = VideoStatus.REJECTED
        asset.validation_error = error.code
        asset.file_size_bytes = written
        _commit(session, "validation_rejected")
        storage.remove_upload(stored_filename)
        logger.info("event=response_returned asset_id=%s status=rejected code=%s", asset.id, error.code)
        raise _error(status.HTTP_422_UNPROCESSABLE_ENTITY, error.code, str(error)) from error
    except SQLAlchemyError as error:
        storage.remove_upload(stored_filename)
        logger.exception("event=response_returned status=database_error")
        raise _error(status.HTTP_500_INTERNAL_SERVER_ERROR, "storage_error", "Upload metadata could not be saved.") from error
    except OSError as error:
        asset.status = VideoStatus.REJECTED
        asset.validation_error = "storage_error"
        _commit(session, "storage_rejected")
        storage.remove_upload(stored_filename)
        logger.info("event=response_returned asset_id=%s status=rejected code=storage_error", asset.id)
        raise _error(status.HTTP_507_INSUFFICIENT_STORAGE, "storage_error", "Upload could not be stored.") from error
    finally:
        await file.close()


@router.get("", response_model=list[VideoResponse])
def list_videos(session: Session = Depends(get_db)) -> list[VideoResponse]:
    records = session.scalars(select(VideoAsset).where(VideoAsset.status != VideoStatus.DELETED).order_by(VideoAsset.created_at.desc())).all()
    return [VideoResponse.model_validate(record) for record in records]


@router.get("/{video_id}", response_model=VideoResponse)
def get_video(video_id: str, session: Session = Depends(get_db)) -> VideoResponse:
    record = session.get(VideoAsset, video_id)
    if record is None or record.status == VideoStatus.DELETED:
        raise _error(status.HTTP_404_NOT_FOUND, "video_not_found", "Video was not found.")
    return VideoResponse.model_validate(record)


@router.delete("/{video_id}", response_model=DeleteVideoResponse)
def delete_video(video_id: str, session: Session = Depends(get_db), storage: StorageService = Depends(get_storage)) -> DeleteVideoResponse:
    record = session.get(VideoAsset, video_id)
    if record is None:
        raise _error(status.HTTP_404_NOT_FOUND, "video_not_found", "Video was not found.")
    if record.status == VideoStatus.DELETED:
        return DeleteVideoResponse(id=record.id, status=record.status, already_deleted=True)
    storage.remove_upload(record.stored_filename)
    record.status = VideoStatus.DELETED
    session.commit()
    return DeleteVideoResponse(id=record.id, status=record.status, already_deleted=False)
