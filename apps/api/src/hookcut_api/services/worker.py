from __future__ import annotations

import logging
import json
import threading
import time
from datetime import UTC, datetime
from pathlib import Path, PurePath
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from hookcut_api.config import Settings
from hookcut_api.models import AudioArtifact, AudioArtifactStatus, ClipCandidate, ClipSelectionRun, JobState, JobType, ProcessingJob, Transcript, TranscriptSegment, TranscriptStatus, TranscriptWord
from hookcut_api.services.clip_selection import CandidateWindow, ClipAnalysisProvider, LocalSelectionEngine, ProviderCandidate, SegmentEvidence
from hookcut_api.services.audio_extraction import AudioExtractionError, AudioMetadata, extract_audio, probe_audio
from hookcut_api.services.jobs import JobTransitionError, recover_interrupted_jobs, source_ready, transition
from hookcut_api.services.storage import StorageService
from hookcut_api.services.transcription import ProviderError, TranscriptionProvider, TranscriptionProviderRegistry, build_provider_registry

logger = logging.getLogger(__name__)


class LocalJobWorker:
    """One local worker thread. It processes only jobs explicitly created through the API."""

    def __init__(self, session_factory: sessionmaker[Session], storage: StorageService, settings: Settings, providers: TranscriptionProviderRegistry | None = None, clip_analysis_providers: dict[str, ClipAnalysisProvider] | None = None) -> None:
        self._sessions = session_factory
        self._storage = storage
        self._settings = settings
        self._providers = providers or build_provider_registry(settings)
        self._clip_analysis_providers = clip_analysis_providers or {}
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
        transition(job, JobState.LOADING_TRANSCRIPT if job.job_type == JobType.CLIP_SELECTION else JobState.VALIDATING_SOURCE, "loading_transcript" if job.job_type == JobType.CLIP_SELECTION else "validating_source", 0)
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
        if job.job_type == JobType.CLIP_SELECTION:
            self._process_clip_selection(session, job)
            return
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

    def _process_clip_selection(self, session: Session, job: ProcessingJob) -> None:
        run = session.scalars(select(ClipSelectionRun).where(ClipSelectionRun.job_id == job.id)).first()
        if run is None:
            job.state = JobState.FAILED; job.current_stage = "failed"; job.error_code = "selection_run_unavailable"; session.commit(); return
        try:
            transcript = session.get(Transcript, run.transcript_id)
            if transcript is None or transcript.status != TranscriptStatus.READY:
                raise ProviderError("transcript_unavailable", "A ready transcript is required for clip selection.")
            segments = [SegmentEvidence(index=item.segment_index, start_seconds=item.start_seconds, end_seconds=item.end_seconds, text=item.text, confidence=item.confidence) for item in session.scalars(select(TranscriptSegment).where(TranscriptSegment.transcript_id == transcript.id).order_by(TranscriptSegment.segment_index)).all()]
            if not segments:
                raise ProviderError("transcript_unavailable", "The transcript has no timestamped segments.")
            engine = LocalSelectionEngine()
            existing = session.scalars(select(ClipCandidate).where(ClipCandidate.selection_run_id == run.id)).all()
            transition(job, JobState.GENERATING_CANDIDATES, "generating_candidates", 15)
            if not existing:
                windows, rejected = engine.generate_windows(segments, run.requested_clip_count, run.duration_mode)
                for window, reason in rejected:
                    analysis = engine.local_analysis(window, run.platform)
                    self._save_candidate(session, run, window, analysis, "rejected", reason, "local_pre_filter")
                for window in windows:
                    analysis = engine.local_analysis(window, run.platform)
                    self._save_candidate(session, run, window, analysis, "candidate", None, "awaiting_provider_analysis")
                session.commit()
                existing = session.scalars(select(ClipCandidate).where(ClipCandidate.selection_run_id == run.id)).all()
            transition(job, JobState.OPTIMIZING_BOUNDARIES, "optimizing_boundaries", 30)
            run.candidate_count = len(existing)
            provider = self._clip_analysis_providers.get(run.provider)
            if provider is None or not provider.is_configured():
                raise ProviderError("provider_not_configured", "The selected clip-analysis provider is not configured.")
            transition(job, JobState.ESTIMATING_COST, "estimating_cost", 35)
            estimate = provider.estimate_cost(len(existing), transcript.duration_seconds)
            job.estimated_cost_usd = estimate; run.estimated_cost_usd = estimate
            if not job.cost_approved:
                transition(job, JobState.AWAITING_COST_APPROVAL, "awaiting_cost_approval")
                job.error_code = "estimated_cost_requires_approval" if estimate is None else "cost_approval_required"
                job.error_message = "Explicit approval is required before Gemini clip analysis."
                run.status = "awaiting_cost_approval"; session.commit(); return
            active = [item for item in existing if item.selection_status == "candidate"]
            windows = [CandidateWindow(item.id, item.start_seconds, item.end_seconds, item.transcript_text, 0, 0, ["segment timing only"]) for item in active]
            shortlist, shortlist_reasons = engine.shortlist(
                windows, run.requested_clip_count, self._settings.gemini_clip_analysis_max_candidates_per_request,
            )
            shortlist_ids = {item.id for item in shortlist}
            for item in active:
                if item.id not in shortlist_ids:
                    item.selection_status = "reserve"
                    item.selection_reason = shortlist_reasons[item.id]
            active = [item for item in active if item.id in shortlist_ids]
            transition(job, JobState.ANALYZING_CANDIDATES, "analyzing_candidates")
            session.commit()
            analyses = provider.analyze_candidates(shortlist, transcript.detected_language, run.platform)
            if self._cancelled(session, job.id):
                transition(job, JobState.CANCELLED, "cancelled")
                run.status = "cancelled"
                session.commit()
                return
            by_id = {item.candidate_id: item for item in analyses}
            for item in active:
                analysis = by_id[item.id]
                self._apply_analysis(item, analysis)
            transition(job, JobState.SCORING_HOOKS, "scoring_hooks", 55)
            transition(job, JobState.ESTIMATING_RETENTION, "estimating_retention", 65)
            transition(job, JobState.DEDUPLICATING, "deduplicating", 75)
            accepted: list[CandidateWindow] = []
            ranked = sorted(active, key=lambda item: (item.viral_potential_score, item.hook_score, item.retention_score), reverse=True)
            for item in ranked:
                window = CandidateWindow(item.id, item.start_seconds, item.end_seconds, item.transcript_text, 0, 0, [])
                duplicate = engine.duplicate_reason(window, accepted)
                if duplicate and run.diversity_mode == "strict":
                    item.selection_status = "rejected"; item.similarity_group, item.rejection_reason = duplicate
                else:
                    accepted.append(window)
            transition(job, JobState.SELECTING_FINAL_SET, "selecting_final_set", 85)
            remaining = [item for item in ranked if item.selection_status == "candidate"]
            selected: list[ClipCandidate] = []
            threshold = 70.0 if run.selection_mode == "highest_potential" else 55.0
            for item in remaining:
                if len(selected) < run.requested_clip_count and item.viral_potential_score >= threshold:
                    item.selection_status = "selected"; item.selection_reason = "Selected from estimated hook, retention, and diversity evidence."; selected.append(item)
                else:
                    item.selection_status = "reserve"; item.selection_reason = "Reserve candidate; not selected in the final set."
                    if run.selection_mode == "exact_count" and len(selected) < run.requested_clip_count:
                        item.selection_status = "selected"; item.selection_reason = "Selected as a weaker Exact Count backup."; selected.append(item)
            run.selected_count = sum(item.selection_status == "selected" for item in existing)
            run.reserve_count = sum(item.selection_status == "reserve" for item in existing)
            run.rejected_count = sum(item.selection_status == "rejected" for item in existing)
            run.status = "completed"; run.completed_at = datetime.now(UTC); run.actual_cost_usd = job.actual_cost_usd
            transition(job, JobState.SAVING_RESULTS, "saving_results", 95)
            transition(job, JobState.COMPLETED, "completed", 100)
            session.commit()
        except (ProviderError, JobTransitionError, SQLAlchemyError) as error:
            session.rollback(); current = session.get(ProcessingJob, job.id)
            if current is not None:
                current.state = JobState.CANCELLED if current.cancellation_requested else JobState.FAILED; current.current_stage = "cancelled" if current.cancellation_requested else "failed"; current.error_code = getattr(error, "code", "clip_selection_failed"); current.error_message = "Clip selection did not complete. Retry is available."; current.completed_at = datetime.now(UTC)
                if run is not None: run.status = current.current_stage
                session.commit()
            logger.warning("event=clip_selection_failed job_id=%s exception_type=%s code=%s", job.id, type(error).__name__, getattr(error, "code", "clip_selection_failed"))

    def _save_candidate(self, session: Session, run: ClipSelectionRun, window: CandidateWindow, analysis: ProviderCandidate, status: str, rejection: str | None, reason: str) -> None:
        candidate = ClipCandidate(id=str(uuid4()), selection_run_id=run.id, video_id=run.video_id, transcript_id=run.transcript_id, start_seconds=window.start_seconds, end_seconds=window.end_seconds, duration_seconds=window.duration_seconds, timestamp_precision="segment", transcript_text=window.transcript_text, topic=analysis.topic, summary=analysis.summary, hook_type=analysis.hook_type, hook_text=analysis.hook_text, hook_score=analysis.hook_score, hook_reason=analysis.hook_reason, first_1_second_score=analysis.first_1_second_score, first_3_seconds_score=analysis.first_3_seconds_score, first_5_seconds_score=analysis.first_5_seconds_score, retention_score=analysis.retention_score, retention_reason=analysis.retention_reason, standalone_score=analysis.standalone_score, usefulness_score=analysis.usefulness_score, entertainment_score=analysis.entertainment_score, emotional_impact_score=analysis.emotional_impact_score, share_potential_score=analysis.share_potential_score, save_potential_score=analysis.save_potential_score, comment_potential_score=analysis.comment_potential_score, loop_potential_score=analysis.loop_potential_score, visual_suitability_score=analysis.visual_suitability_score, viral_potential_score=analysis.viral_potential_score, confidence_score=analysis.confidence_score, ideal_platform=analysis.ideal_platform, target_audience=analysis.target_audience, likely_viewer_reaction=analysis.likely_viewer_reaction, suggested_title=analysis.suggested_title, suggested_on_screen_hook=analysis.suggested_on_screen_hook, detected_weaknesses=json.dumps(analysis.detected_weaknesses), boundary_mode="balanced_segment", selection_status=status, selection_reason=reason, rejection_reason=rejection)
        session.add(candidate)

    def _apply_analysis(self, item: ClipCandidate, analysis: ProviderCandidate) -> None:
        for name in ("topic", "summary", "hook_type", "hook_text", "hook_score", "hook_reason", "first_1_second_score", "first_3_seconds_score", "first_5_seconds_score", "retention_score", "retention_reason", "standalone_score", "usefulness_score", "entertainment_score", "emotional_impact_score", "share_potential_score", "save_potential_score", "comment_potential_score", "loop_potential_score", "visual_suitability_score", "confidence_score", "ideal_platform", "target_audience", "likely_viewer_reaction", "suggested_title", "suggested_on_screen_hook"):
            setattr(item, name, getattr(analysis, name))
        item.viral_potential_score = analysis.viral_potential_score
        item.detected_weaknesses = json.dumps(analysis.detected_weaknesses)
