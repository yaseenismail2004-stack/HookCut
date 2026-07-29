from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from hookcut_api.models import JobState, ProcessingJob, Transcript, VideoAsset, VideoStatus

logger = logging.getLogger(__name__)

ACTIVE_STATES = {JobState.QUEUED, JobState.VALIDATING_SOURCE, JobState.EXTRACTING_AUDIO, JobState.AUDIO_READY, JobState.ESTIMATING_COST, JobState.AWAITING_COST_APPROVAL, JobState.TRANSCRIBING, JobState.SAVING_TRANSCRIPT}
TRANSITIONS: dict[JobState, set[JobState]] = {
    JobState.QUEUED: {JobState.VALIDATING_SOURCE, JobState.CANCELLED, JobState.FAILED},
    JobState.VALIDATING_SOURCE: {JobState.EXTRACTING_AUDIO, JobState.CANCELLED, JobState.FAILED},
    JobState.EXTRACTING_AUDIO: {JobState.AUDIO_READY, JobState.CANCELLED, JobState.FAILED},
    JobState.AUDIO_READY: {JobState.ESTIMATING_COST, JobState.CANCELLED, JobState.FAILED},
    JobState.ESTIMATING_COST: {JobState.AWAITING_COST_APPROVAL, JobState.TRANSCRIBING, JobState.CANCELLED, JobState.FAILED},
    JobState.AWAITING_COST_APPROVAL: {JobState.QUEUED, JobState.CANCELLED},
    JobState.TRANSCRIBING: {JobState.SAVING_TRANSCRIPT, JobState.CANCELLED, JobState.FAILED},
    JobState.SAVING_TRANSCRIPT: {JobState.COMPLETED, JobState.CANCELLED, JobState.FAILED},
    JobState.COMPLETED: set(), JobState.FAILED: {JobState.QUEUED}, JobState.CANCELLED: {JobState.QUEUED},
}


class JobTransitionError(ValueError):
    pass


def transition(job: ProcessingJob, target: JobState, stage: str, progress: float | None = None) -> None:
    if target not in TRANSITIONS[job.state]:
        raise JobTransitionError(f"Invalid job state transition: {job.state} to {target}.")
    previous = job.state
    job.state = target
    job.current_stage = stage
    if progress is not None:
        job.progress_percent = progress
    if target in {JobState.VALIDATING_SOURCE, JobState.EXTRACTING_AUDIO} and job.started_at is None:
        job.started_at = datetime.now(UTC)
    if target in {JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED}:
        job.completed_at = datetime.now(UTC)
    logger.info("event=job_state_transition job_id=%s video_id=%s from_state=%s to_state=%s stage=%s", job.id, job.video_id, previous, target, stage)


def active_job_for_video(session: Session, video_id: str) -> ProcessingJob | None:
    return session.scalars(select(ProcessingJob).where(ProcessingJob.video_id == video_id, ProcessingJob.state.in_(ACTIVE_STATES))).first()


def recover_interrupted_jobs(session: Session) -> int:
    interrupted = session.scalars(select(ProcessingJob).where(ProcessingJob.state.in_({JobState.VALIDATING_SOURCE, JobState.EXTRACTING_AUDIO, JobState.AUDIO_READY, JobState.ESTIMATING_COST, JobState.TRANSCRIBING, JobState.SAVING_TRANSCRIPT}))).all()
    for job in interrupted:
        job.state = JobState.FAILED
        job.current_stage = "interrupted"
        job.error_code = "worker_interrupted"
        job.error_message = "Processing was interrupted by an application restart. Retry is available."
        job.completed_at = datetime.now(UTC)
    if interrupted:
        session.commit()
    return len(interrupted)


def source_ready(session: Session, video_id: str) -> VideoAsset | None:
    video = session.get(VideoAsset, video_id)
    return video if video is not None and video.status == VideoStatus.READY else None


def transcript_for_video(session: Session, video_id: str) -> Transcript | None:
    return session.scalars(select(Transcript).where(Transcript.video_id == video_id, Transcript.status == "ready").order_by(Transcript.created_at.desc())).first()
