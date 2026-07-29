from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from hookcut_api.models import ClipCandidate, ClipSelectionRun, JobState, JobType, ProcessingJob
from hookcut_api.routers.jobs import get_db
from hookcut_api.schemas import ClipCandidateResponse, ClipSelectionJobRequest, ClipSelectionRunResponse, JobResponse, ManualSelectionRequest
from hookcut_api.services.clip_selection import DIVERSITY_MODES, DURATION_MODES, PLATFORMS, SELECTION_MODES, duration_limits
from hookcut_api.services.jobs import ACTIVE_STATES, source_ready, transcript_for_video

router = APIRouter(tags=["clip selection"])


def _error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def _run_response(run: ClipSelectionRun) -> ClipSelectionRunResponse:
    return ClipSelectionRunResponse.model_validate(run)


def _candidate_response(item: ClipCandidate) -> ClipCandidateResponse:
    return ClipCandidateResponse(id=item.id, selection_run_id=item.selection_run_id, start_seconds=item.start_seconds, end_seconds=item.end_seconds, duration_seconds=item.duration_seconds, timestamp_precision=item.timestamp_precision, transcript_text=item.transcript_text, topic=item.topic, summary=item.summary, hook_type=item.hook_type, hook_text=item.hook_text, hook_score=item.hook_score, first_1_second_score=item.first_1_second_score, first_3_seconds_score=item.first_3_seconds_score, first_5_seconds_score=item.first_5_seconds_score, retention_score=item.retention_score, retention_reason=item.retention_reason, viral_potential_score=item.viral_potential_score, confidence_score=item.confidence_score, ideal_platform=item.ideal_platform, suggested_title=item.suggested_title, suggested_on_screen_hook=item.suggested_on_screen_hook, detected_weaknesses=json.loads(item.detected_weaknesses), boundary_mode=item.boundary_mode, selection_status=item.selection_status, selection_reason=item.selection_reason, rejection_reason=item.rejection_reason, similarity_group=item.similarity_group)


@router.post("/api/videos/{video_id}/clip-selection-jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_clip_selection_job(video_id: str, payload: ClipSelectionJobRequest, request: Request, session: Session = Depends(get_db)) -> JobResponse:
    if payload.platform not in PLATFORMS or payload.duration_mode not in DURATION_MODES or payload.selection_mode not in SELECTION_MODES or payload.diversity_mode not in DIVERSITY_MODES:
        raise _error(status.HTTP_422_UNPROCESSABLE_ENTITY, "invalid_selection_settings", "Clip selection settings are invalid.")
    video = source_ready(session, video_id)
    transcript = transcript_for_video(session, video_id)
    if video is None:
        raise _error(status.HTTP_409_CONFLICT, "source_not_ready", "The source video is not ready.")
    if transcript is None:
        raise _error(status.HTTP_409_CONFLICT, "transcript_unavailable", "A completed transcript is required.")
    duplicate = session.scalars(select(ProcessingJob).where(ProcessingJob.video_id == video_id, ProcessingJob.job_type == JobType.CLIP_SELECTION, ProcessingJob.state.in_(ACTIVE_STATES))).first()
    if duplicate is not None:
        raise _error(status.HTTP_409_CONFLICT, "duplicate_active_job", "An equivalent clip-selection job is already active.")
    providers = cast(dict[str, object], request.app.state.clip_analysis_providers)
    provider = providers.get("gemini")
    if provider is None or not getattr(provider, "is_configured")():
        raise _error(status.HTTP_503_SERVICE_UNAVAILABLE, "provider_not_configured", "Gemini clip analysis is not configured.")
    job = ProcessingJob(id=str(uuid4()), video_id=video_id, job_type=JobType.CLIP_SELECTION, state=JobState.QUEUED, progress_percent=0, current_stage="queued", language_mode="auto", transcription_provider="gemini", transcription_model=getattr(provider, "model_name"), retry_count=0, max_retries=1, cancellation_requested=False, cost_approved=payload.approve_estimated_cost)
    minimum, maximum = duration_limits(payload.duration_mode)
    run = ClipSelectionRun(id=str(uuid4()), video_id=video_id, transcript_id=transcript.id, job_id=job.id, requested_clip_count=payload.requested_clip_count, platform=payload.platform, duration_mode=payload.duration_mode, minimum_duration_seconds=minimum, maximum_duration_seconds=maximum, selection_mode=payload.selection_mode, diversity_mode=payload.diversity_mode, provider="gemini", model=getattr(provider, "model_name"), status="queued")
    session.add_all([job, run]); session.commit(); session.refresh(job)
    return JobResponse(id=job.id, video_id=job.video_id, state=str(job.state), current_stage=job.current_stage, progress_percent=job.progress_percent, progress_indeterminate=False, estimated_cost_usd=job.estimated_cost_usd, cost_approval_required=False, retry_available=False, cancellation_available=True, error_code=None, error_key=None, created_at=job.created_at, started_at=job.started_at, completed_at=job.completed_at)


@router.get("/api/videos/{video_id}/clip-selection-runs/latest", response_model=ClipSelectionRunResponse)
def latest_run(video_id: str, session: Session = Depends(get_db)) -> ClipSelectionRunResponse:
    run = session.scalars(select(ClipSelectionRun).where(ClipSelectionRun.video_id == video_id).order_by(ClipSelectionRun.created_at.desc())).first()
    if run is None: raise _error(404, "selection_run_not_found", "No clip-selection run exists.")
    return _run_response(run)


@router.get("/api/clip-selection-runs/{run_id}", response_model=ClipSelectionRunResponse)
def get_run(run_id: str, session: Session = Depends(get_db)) -> ClipSelectionRunResponse:
    run = session.get(ClipSelectionRun, run_id)
    if run is None: raise _error(404, "selection_run_not_found", "Clip-selection run was not found.")
    return _run_response(run)


@router.get("/api/clip-selection-runs/{run_id}/candidates", response_model=list[ClipCandidateResponse])
def list_candidates(run_id: str, selection_status: str = "all", session: Session = Depends(get_db)) -> list[ClipCandidateResponse]:
    query = select(ClipCandidate).where(ClipCandidate.selection_run_id == run_id)
    if selection_status != "all": query = query.where(ClipCandidate.selection_status == selection_status)
    return [_candidate_response(item) for item in session.scalars(query.order_by(ClipCandidate.viral_potential_score.desc())).all()]


@router.get("/api/clip-candidates/{candidate_id}", response_model=ClipCandidateResponse)
def get_candidate(candidate_id: str, session: Session = Depends(get_db)) -> ClipCandidateResponse:
    item = session.get(ClipCandidate, candidate_id)
    if item is None: raise _error(404, "candidate_not_found", "Candidate was not found.")
    return _candidate_response(item)


@router.post("/api/clip-selection-runs/{run_id}/approve-cost", response_model=JobResponse)
def approve_selection_cost(run_id: str, session: Session = Depends(get_db)) -> JobResponse:
    run = session.get(ClipSelectionRun, run_id)
    if run is None: raise _error(404, "selection_run_not_found", "Clip-selection run was not found.")
    job = session.get(ProcessingJob, run.job_id)
    if job is None or job.state != JobState.AWAITING_COST_APPROVAL: raise _error(409, "cost_approval_not_required", "Cost approval is not required.")
    job.cost_approved = True; job.state = JobState.QUEUED; job.current_stage = "queued"; job.error_code = None; job.error_message = None; run.status = "queued"; session.commit()
    return JobResponse(id=job.id, video_id=job.video_id, state=str(job.state), current_stage=job.current_stage, progress_percent=job.progress_percent, progress_indeterminate=False, estimated_cost_usd=job.estimated_cost_usd, cost_approval_required=False, retry_available=False, cancellation_available=True, error_code=None, error_key=None, created_at=job.created_at, started_at=job.started_at, completed_at=job.completed_at)


@router.post("/api/clip-selection-runs/{run_id}/cancel", response_model=JobResponse)
def cancel_selection(run_id: str, session: Session = Depends(get_db)) -> JobResponse:
    run = session.get(ClipSelectionRun, run_id); job = session.get(ProcessingJob, run.job_id) if run else None
    if run is None or job is None: raise _error(404, "selection_run_not_found", "Clip-selection run was not found.")
    job.cancellation_requested = True
    if job.state in {JobState.QUEUED, JobState.AWAITING_COST_APPROVAL}: job.state = JobState.CANCELLED; job.current_stage = "cancelled"; job.completed_at = datetime.now(UTC); run.status = "cancelled"
    session.commit()
    return JobResponse(id=job.id, video_id=job.video_id, state=str(job.state), current_stage=job.current_stage, progress_percent=job.progress_percent, progress_indeterminate=False, estimated_cost_usd=job.estimated_cost_usd, cost_approval_required=False, retry_available=job.retry_count < job.max_retries, cancellation_available=False, error_code=job.error_code, error_key=job.error_code, created_at=job.created_at, started_at=job.started_at, completed_at=job.completed_at)


@router.post("/api/clip-selection-runs/{run_id}/retry", response_model=JobResponse)
def retry_selection(run_id: str, session: Session = Depends(get_db)) -> JobResponse:
    run = session.get(ClipSelectionRun, run_id)
    job = session.get(ProcessingJob, run.job_id) if run else None
    if run is None or job is None:
        raise _error(404, "selection_run_not_found", "Clip-selection run was not found.")
    if job.state not in {JobState.FAILED, JobState.CANCELLED}:
        raise _error(409, "retry_not_available", "This selection job is not retryable.")
    if job.retry_count >= job.max_retries:
        raise _error(409, "retry_limit_reached", "The retry limit has been reached.")
    job.retry_count += 1
    job.cancellation_requested = False
    job.error_code = None
    job.error_message = None
    job.completed_at = None
    job.state = JobState.QUEUED
    job.current_stage = "queued"
    run.status = "queued"
    session.commit()
    return JobResponse(id=job.id, video_id=job.video_id, state=str(job.state), current_stage=job.current_stage, progress_percent=job.progress_percent, progress_indeterminate=False, estimated_cost_usd=job.estimated_cost_usd, cost_approval_required=False, retry_available=False, cancellation_available=True, error_code=None, error_key=None, created_at=job.created_at, started_at=job.started_at, completed_at=job.completed_at)


@router.patch("/api/clip-candidates/{candidate_id}/selection", response_model=ClipCandidateResponse)
def manual_selection(candidate_id: str, payload: ManualSelectionRequest, session: Session = Depends(get_db)) -> ClipCandidateResponse:
    if payload.selection_status not in {"selected", "reserve", "manually_selected", "manually_rejected"}: raise _error(422, "invalid_selection_status", "Manual selection status is invalid.")
    item = session.get(ClipCandidate, candidate_id)
    if item is None: raise _error(404, "candidate_not_found", "Candidate was not found.")
    run = session.get(ClipSelectionRun, item.selection_run_id)
    if run is None: raise _error(404, "selection_run_not_found", "Clip-selection run was not found.")
    selected = session.scalars(select(ClipCandidate).where(ClipCandidate.selection_run_id == run.id, ClipCandidate.selection_status.in_({"selected", "manually_selected"}))).all()
    if payload.selection_status in {"selected", "manually_selected"} and item not in selected and len(selected) >= run.requested_clip_count: raise _error(409, "selection_limit_reached", "Remove a selected candidate before adding another.")
    item.selection_status = payload.selection_status; item.selection_reason = f"Manual adjustment: {item.selection_reason}"; run.selected_count = sum(candidate.selection_status in {"selected", "manually_selected"} for candidate in session.scalars(select(ClipCandidate).where(ClipCandidate.selection_run_id == run.id)).all()); session.commit()
    return _candidate_response(item)
