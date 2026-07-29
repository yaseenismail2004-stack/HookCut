from __future__ import annotations

import logging
import threading
import time
from datetime import UTC, datetime
from pathlib import Path, PurePath
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from hookcut_api.config import Settings
from hookcut_api.models import AudioArtifact, AudioArtifactStatus, JobState, ProcessingJob, Transcript, TranscriptSegment, TranscriptStatus, TranscriptWord
from hookcut_api.services.audio_extraction import AudioExtractionError, AudioMetadata, extract_audio, probe_audio
from hookcut_api.services.jobs import JobTransitionError, recover_interrupted_jobs, source_ready, transition
from hookcut_api.services.storage import StorageService
from hookcut_api.services.transcription import ProviderError, TranscriptionProvider, TranscriptionProviderRegistry, build_provider_registry

logger = logging.getLogger(__name__)


class LocalJobWorker:
    """One local worker thread. It processes only jobs explicitly created through the API."""

    def __init__(self, session_factory: sessionmaker[Session], storage: StorageService, settings: Settings, providers: TranscriptionProviderRegistry | None = None) -> None:
        self._sessions = session_factory
        self._storage = storage
        self._settings = settings
        self._providers = providers or build_provider_registry(settings)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def start(self) -> None:
        with self._sessions() as session:
            recovered = recover_interrupted_jobs(session)
            if recovered:
                logger.warning("event=worker_recovered_interrupted_jobs count=%s", recovered)
        self._thread = threading.Thread(target=self._run, name="hookcut-local-worker", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _run(self) -> None:
        while not self._stop.wait(self._settings.worker_poll_interval_seconds):
            try:
                self.process_once()
            except Exception:
                logger.exception("event=worker_iteration_failed")

    def _claim(self, session: Session) -> ProcessingJob | None:
        job = session.scalars(select(ProcessingJob).where(ProcessingJob.state == JobState.QUEUED).order_by(ProcessingJob.created_at).limit(1)).first()
        if job is None:
            return None
        if job.cancellation_requested:
            transition(job, JobState.CANCELLED, "cancelled")
            session.commit()
            return None
        transition(job, JobState.VALIDATING_SOURCE, "validating_source", 0)
        session.commit()
        return job

    def process_once(self) -> bool:
        with self._sessions() as session:
            job = self._claim(session)
            if job is None:
                return False
            self._process(session, job)
            return True

    def _cancelled(self, session: Session, job_id: str) -> bool:
        session.expire_all()
        job = session.get(ProcessingJob, job_id)
        return self._stop.is_set() or bool(job and job.cancellation_requested)

    def _reusable_audio(self, session: Session, job: ProcessingJob) -> tuple[AudioArtifact, Path, AudioMetadata] | None:
        """Return one validated ready artifact for a resumed job without duplication."""
        artifact = session.scalars(
            select(AudioArtifact)
            .where(AudioArtifact.job_id == job.id, AudioArtifact.status == AudioArtifactStatus.READY)
            .order_by(AudioArtifact.created_at.desc())
            .limit(1)
        ).first()
        if artifact is None:
            return None
        try:
            destination = self._storage.resolve(PurePath("audio") / artifact.stored_filename)
            metadata = probe_audio(destination)
        except (AudioExtractionError, OSError):
            self._storage.remove_audio(artifact.stored_filename)
            artifact.status = AudioArtifactStatus.DELETED
            artifact.deleted_at = datetime.now(UTC)
            session.commit()
            return None
        artifact.duration_seconds = metadata.duration_seconds
        artifact.codec = metadata.codec
        artifact.sample_rate = metadata.sample_rate
        artifact.channels = metadata.channels
        artifact.file_size_bytes = metadata.file_size_bytes
        session.commit()
        logger.info("event=audio_reused_for_resume job_id=%s", job.id)
        return artifact, destination, metadata

    def _process(self, session: Session, job: ProcessingJob) -> None:
        audio: AudioArtifact | None = None
        try:
            provider = self._providers.get(job.transcription_provider)
            if provider is None or not provider.is_configured():
                raise ProviderError("provider_not_configured", "The selected transcription provider is not configured.")
            video = source_ready(session, job.video_id)
            if video is None:
                raise AudioExtractionError("source_not_ready", "The source video is unavailable or not ready.")
            source = self._storage.resolve(Path("uploads") / video.stored_filename)
            if not source.is_file():
                raise AudioExtractionError("source_not_ready", "The source video is unavailable.")
            if self._cancelled(session, job.id):
                transition(job, JobState.CANCELLED, "cancelled")
                session.commit(); return
            transition(job, JobState.EXTRACTING_AUDIO, "extracting_audio", 0)
            reusable = self._reusable_audio(session, job)
            if reusable is None:
                stored_filename, destination = self._storage.new_audio_path()
                audio = AudioArtifact(id=str(uuid4()), video_id=job.video_id, job_id=job.id, stored_filename=stored_filename, file_size_bytes=0, status=AudioArtifactStatus.EXTRACTING)
                session.add(audio); session.commit()
                metadata = extract_audio(source, destination, float(video.duration_seconds or 0), lambda value: self._update_progress(session, job.id, value), lambda: self._cancelled(session, job.id))
            else:
                audio, destination, metadata = reusable
                stored_filename = audio.stored_filename
            if self._cancelled(session, job.id):
                self._storage.remove_audio(stored_filename)
                audio.status = AudioArtifactStatus.DELETED; audio.deleted_at = datetime.now(UTC)
                transition(job, JobState.CANCELLED, "cancelled")
                session.commit(); return
            audio.duration_seconds = metadata.duration_seconds; audio.codec = metadata.codec; audio.sample_rate = metadata.sample_rate; audio.channels = metadata.channels; audio.file_size_bytes = metadata.file_size_bytes; audio.status = AudioArtifactStatus.READY
            transition(job, JobState.AUDIO_READY, "audio_ready", 100); transition(job, JobState.ESTIMATING_COST, "estimating_cost")
            estimate = provider.estimate_cost(metadata.duration_seconds)
            job.estimated_cost_usd = estimate
            allowed = float(video.duration_seconds or 0) / 3600 * float(self._settings.max_ai_cost_per_video_hour_usd)
            if (estimate is None and not job.cost_approved) or (estimate is not None and estimate > allowed and not job.cost_approved):
                transition(job, JobState.AWAITING_COST_APPROVAL, "awaiting_cost_approval")
                job.error_code = "estimated_cost_requires_approval" if estimate is None else "cost_limit_exceeded"
                job.error_message = "Explicit approval is required before a paid transcription request."
                session.commit(); return
            transition(job, JobState.TRANSCRIBING, "transcribing")
            session.commit()
            result = provider.transcribe(destination, job.language_mode)
            if self._cancelled(session, job.id):
                self._storage.remove_audio(stored_filename); audio.status = AudioArtifactStatus.DELETED; audio.deleted_at = datetime.now(UTC); transition(job, JobState.CANCELLED, "cancelled"); session.commit(); return
            transition(job, JobState.SAVING_TRANSCRIPT, "saving_transcript")
            transcript = Transcript(id=str(uuid4()), video_id=job.video_id, job_id=job.id, provider=result.provider, model=result.model, detected_language=result.detected_language, language_confidence=result.language_confidence, full_text=result.full_text, duration_seconds=result.duration_seconds, status=TranscriptStatus.READY)
            session.add(transcript); session.flush()
            for part in result.segments:
                session.add(TranscriptSegment(id=str(uuid4()), transcript_id=transcript.id, segment_index=part.index, start_seconds=part.start_seconds, end_seconds=part.end_seconds, text=part.text, confidence=part.confidence))
            for part in result.words:
                session.add(TranscriptWord(id=str(uuid4()), transcript_id=transcript.id, segment_id=None, word_index=part.index, start_seconds=part.start_seconds, end_seconds=part.end_seconds, text=part.text, confidence=part.confidence))
            job.actual_cost_usd = result.cost_usd
            transition(job, JobState.COMPLETED, "completed", 100)
            self._storage.remove_audio(stored_filename); audio.status = AudioArtifactStatus.DELETED; audio.deleted_at = datetime.now(UTC)
            session.commit()
            logger.info("event=job_completed job_id=%s video_id=%s", job.id, job.video_id)
        except (AudioExtractionError, ProviderError, JobTransitionError) as error:
            session.rollback()
            current = session.get(ProcessingJob, job.id)
            if current is not None:
                if current.cancellation_requested or getattr(error, "code", "") == "job_cancelled":
                    current.state = JobState.CANCELLED; current.current_stage = "cancelled"
                else:
                    current.state = JobState.FAILED; current.current_stage = "failed"; current.error_code = getattr(error, "code", "transcription_failed"); current.error_message = str(error)[:512]
                current.completed_at = datetime.now(UTC); session.commit()
            if audio is not None and audio.status == AudioArtifactStatus.EXTRACTING:
                self._storage.remove_audio(audio.stored_filename)
            logger.warning("event=job_failed job_id=%s code=%s", job.id, getattr(error, "code", "transcription_failed"))
        except Exception:
            session.rollback(); current = session.get(ProcessingJob, job.id)
            if current is not None:
                current.state = JobState.FAILED; current.current_stage = "failed"; current.error_code = "transcription_failed"; current.error_message = "Processing failed unexpectedly."; current.completed_at = datetime.now(UTC); session.commit()
            if audio is not None and audio.status == AudioArtifactStatus.EXTRACTING:
                self._storage.remove_audio(audio.stored_filename)
            logger.exception("event=job_failed job_id=%s code=transcription_failed", job.id)

    def _update_progress(self, session: Session, job_id: str, value: float) -> None:
        job = session.get(ProcessingJob, job_id)
        if job is not None and job.state == JobState.EXTRACTING_AUDIO:
            job.progress_percent = round(value, 1)
            session.commit()
