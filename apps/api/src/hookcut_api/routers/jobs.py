from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from hookcut_api.models import JobState, JobType, ProcessingJob, Transcript, TranscriptSegment, TranscriptWord
from hookcut_api.schemas import JobResponse, TranscriptPartResponse, TranscriptResponse, TranscriptionJobRequest
from hookcut_api.services.jobs import ACTIVE_STATES, active_job_for_video, source_ready
from hookcut_api.services.transcription import TranscriptionProviderRegistry

router = APIRouter(tags=["processing"])


def _error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def get_db(request: Request) -> Generator[Session, None, None]:
    session: Session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


def get_providers(request: Request) -> TranscriptionProviderRegistry:
    return cast(TranscriptionProviderRegistry, request.app.state.transcription_providers)


def _job_response(job: ProcessingJob) -> JobResponse:
    return JobResponse(id=job.id, video_id=job.video_id, state=str(job.state), current_stage=job.current_stage, progress_percent=job.progress_percent, progress_indeterminate=job.state in {JobState.TRANSCRIBING, JobState.SAVING_TRANSCRIPT}, estimated_cost_usd=job.estimated_cost_usd, cost_approval_required=job.state == JobState.AWAITING_COST_APPROVAL, retry_available=job.state in {JobState.FAILED, JobState.CANCELLED} and job.retry_count < job.max_retries, cancellation_available=job.state in ACTIVE_STATES and job.state != JobState.AWAITING_COST_APPROVAL, error_code=job.error_code, error_key=job.error_code, created_at=job.created_at, started_at=job.started_at, completed_at=job.completed_at)


@router.post("/api/videos/{video_id}/transcription-jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_transcription_job(video_id: str, payload: TranscriptionJobRequest, session: Session = Depends(get_db), providers: TranscriptionProviderRegistry = Depends(get_providers)) -> JobResponse:
    if payload.language_mode not in {"auto", "ar", "en"}:
        raise _error(status.HTTP_422_UNPROCESSABLE_ENTITY, "invalid_language_mode", "Choose automatic, Arabic, or English.")
    provider = providers.get(payload.provider)
    if provider is None:
        raise _error(status.HTTP_422_UNPROCESSABLE_ENTITY, "provider_not_configured", "The requested transcription provider is unavailable.")
    if not provider.is_configured():
        raise _error(status.HTTP_503_SERVICE_UNAVAILABLE, "provider_not_configured", "The selected transcription provider is not configured.")
    if source_ready(session, video_id) is None:
        raise _error(status.HTTP_409_CONFLICT, "source_not_ready", "The source video is not ready for transcription.")
    if active_job_for_video(session, video_id) is not None:
        raise _error(status.HTTP_409_CONFLICT, "duplicate_active_job", "An active transcription job already exists for this video.")
    job = ProcessingJob(id=str(uuid4()), video_id=video_id, job_type=JobType.TRANSCRIPTION, state=JobState.QUEUED, progress_percent=0, current_stage="queued", language_mode=payload.language_mode, transcription_provider=payload.provider, transcription_model=provider.model_name, retry_count=0, max_retries=1, cancellation_requested=False, cost_approved=payload.approve_estimated_cost)
    session.add(job); session.commit(); session.refresh(job)
    return _job_response(job)


@router.get("/api/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str, session: Session = Depends(get_db)) -> JobResponse:
    job = session.get(ProcessingJob, job_id)
    if job is None:
        raise _error(status.HTTP_404_NOT_FOUND, "job_not_found", "Job was not found.")
    return _job_response(job)


@router.get("/api/videos/{video_id}/jobs", response_model=list[JobResponse])
def list_video_jobs(video_id: str, session: Session = Depends(get_db)) -> list[JobResponse]:
    jobs = session.scalars(select(ProcessingJob).where(ProcessingJob.video_id == video_id).order_by(ProcessingJob.created_at.desc())).all()
    return [_job_response(job) for job in jobs]


@router.post("/api/jobs/{job_id}/approve-cost", response_model=JobResponse)
def approve_cost(job_id: str, session: Session = Depends(get_db)) -> JobResponse:
    job = session.get(ProcessingJob, job_id)
    if job is None:
        raise _error(status.HTTP_404_NOT_FOUND, "job_not_found", "Job was not found.")
    if job.state != JobState.AWAITING_COST_APPROVAL:
        raise _error(status.HTTP_409_CONFLICT, "cost_approval_not_required", "This job is not awaiting cost approval.")
    job.cost_approved = True; job.state = JobState.QUEUED; job.current_stage = "queued"; job.error_code = None; job.error_message = None; session.commit()
    return _job_response(job)


@router.post("/api/jobs/{job_id}/cancel", response_model=JobResponse)
def cancel_job(job_id: str, session: Session = Depends(get_db)) -> JobResponse:
    job = session.get(ProcessingJob, job_id)
    if job is None:
        raise _error(status.HTTP_404_NOT_FOUND, "job_not_found", "Job was not found.")
    if job.state in {JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED}:
        raise _error(status.HTTP_409_CONFLICT, "job_not_cancellable", "This job cannot be cancelled.")
    job.cancellation_requested = True
    if job.state in {JobState.QUEUED, JobState.AWAITING_COST_APPROVAL}:
        job.state = JobState.CANCELLED; job.current_stage = "cancelled"; job.completed_at = datetime.now(UTC)
    session.commit()
    return _job_response(job)


@router.post("/api/jobs/{job_id}/retry", response_model=JobResponse)
def retry_job(job_id: str, session: Session = Depends(get_db)) -> JobResponse:
    job = session.get(ProcessingJob, job_id)
    if job is None:
        raise _error(status.HTTP_404_NOT_FOUND, "job_not_found", "Job was not found.")
    if job.state not in {JobState.FAILED, JobState.CANCELLED}:
        raise _error(status.HTTP_409_CONFLICT, "retry_not_available", "This job is not retryable.")
    if job.retry_count >= job.max_retries:
        raise _error(status.HTTP_409_CONFLICT, "retry_limit_reached", "The retry limit has been reached.")
    if session.scalars(select(Transcript).where(Transcript.job_id == job.id, Transcript.status == "ready")).first() is not None:
        raise _error(status.HTTP_409_CONFLICT, "retry_not_available", "A ready transcript already exists.")
    job.retry_count += 1; job.cancellation_requested = False; job.error_code = None; job.error_message = None; job.state = JobState.QUEUED; job.current_stage = "queued"; job.completed_at = None; session.commit()
    return _job_response(job)


@router.get("/api/videos/{video_id}/transcript", response_model=TranscriptResponse)
def get_transcript(video_id: str, session: Session = Depends(get_db)) -> TranscriptResponse:
    transcript = session.scalars(select(Transcript).where(Transcript.video_id == video_id, Transcript.status == "ready").order_by(Transcript.created_at.desc())).first()
    if transcript is None:
        raise _error(status.HTTP_404_NOT_FOUND, "transcript_unavailable", "A transcript is not available yet.")
    segments = session.scalars(select(TranscriptSegment).where(TranscriptSegment.transcript_id == transcript.id).order_by(TranscriptSegment.segment_index)).all()
    words = session.scalars(select(TranscriptWord).where(TranscriptWord.transcript_id == transcript.id).order_by(TranscriptWord.word_index)).all()
    return TranscriptResponse(id=transcript.id, video_id=transcript.video_id, provider=transcript.provider, model=transcript.model, detected_language=transcript.detected_language, language_confidence=transcript.language_confidence, full_text=transcript.full_text, duration_seconds=transcript.duration_seconds, status=str(transcript.status), segments=[TranscriptPartResponse(index=item.segment_index, start_seconds=item.start_seconds, end_seconds=item.end_seconds, text=item.text, confidence=item.confidence) for item in segments], words=[TranscriptPartResponse(index=item.word_index, start_seconds=item.start_seconds, end_seconds=item.end_seconds, text=item.text, confidence=item.confidence) for item in words])
