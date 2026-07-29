from __future__ import annotations

import subprocess
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from hookcut_api.config import Settings
from hookcut_api.db import Base
from hookcut_api.main import create_app
from hookcut_api.models import JobState, JobType, ProcessingJob, VideoAsset, VideoStatus
from hookcut_api.services.jobs import JobTransitionError, transition
from hookcut_api.services.transcription import NormalizedTranscript, TranscriptPart


class FakeProvider:
    provider_name = "openai"
    def __init__(self, estimate: float | None = 0.001, configured: bool = True) -> None: self.estimate = estimate; self.configured = configured
    def is_configured(self) -> bool: return self.configured
    def estimate_cost(self, duration_seconds: float) -> float | None: return self.estimate
    def transcribe(self, audio_path: Path, language_mode: str) -> NormalizedTranscript:
        assert audio_path.suffix == ".flac" and audio_path.is_file()
        return NormalizedTranscript("ar", None, "هلا world", 21.0, [TranscriptPart(0, 0.0, 2.0, "هلا world")], [TranscriptPart(0, 0.0, 0.5, "هلا"), TranscriptPart(1, 0.5, 1.0, "world")], "openai", "fake-test-model", None, None)


def _app(tmp_path: Path, provider: FakeProvider | None = None) -> tuple[object, Settings]:
    database = tmp_path / "pipeline.db"
    settings = Settings(storage_root=str(tmp_path / "storage"), database_url=f"sqlite:///{database.as_posix()}", openai_api_key="test-only", openai_transcription_model="test-model", worker_enabled=False)
    Base.metadata.create_all(create_engine(settings.resolved_database_url))
    app = create_app(settings)
    app.state.transcription_provider = provider or FakeProvider()
    return app, settings


def _ready_video(app: object, settings: Settings, tmp_path: Path) -> str:
    storage = settings.resolved_storage_root; (storage / "uploads").mkdir(parents=True, exist_ok=True)
    stored = f"{uuid4().hex}.mp4"; source = storage / "uploads" / stored
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=320x240:rate=30", "-f", "lavfi", "-i", "sine=frequency=1000:sample_rate=48000", "-t", "21", "-c:v", "libx264", "-c:a", "aac", str(source)], check=True, timeout=60)
    session = app.state.session_factory()
    video_id = str(uuid4())
    session.add(VideoAsset(id=video_id, original_filename="source.mp4", stored_filename=stored, file_size_bytes=source.stat().st_size, container="mov,mp4,m4a,3gp,3g2,mj2", duration_seconds=21, width=320, height=240, frame_rate=30, video_codec="h264", audio_codec="aac", audio_channels=1, audio_sample_rate=48000, status=VideoStatus.READY))
    session.commit(); session.close()
    return video_id


def test_real_audio_pipeline_persists_unicode_transcript(tmp_path: Path) -> None:
    app, settings = _app(tmp_path)
    with TestClient(app) as client:
        video_id = _ready_video(app, settings, tmp_path)
        created = client.post(f"/api/videos/{video_id}/transcription-jobs", json={"language_mode": "auto", "provider": "openai", "approve_estimated_cost": True})
        assert created.status_code == 201
        assert app.state.worker.process_once() is True
        job = client.get(f"/api/jobs/{created.json()['id']}").json()
        assert job["state"] == "completed"
        transcript = client.get(f"/api/videos/{video_id}/transcript").json()
        assert transcript["full_text"] == "هلا world"
        assert transcript["segments"][0]["text"] == "هلا world"
        assert not list((settings.resolved_storage_root / "audio").glob("*.flac"))


def test_cost_approval_and_cancel(tmp_path: Path) -> None:
    app, settings = _app(tmp_path, FakeProvider(estimate=None))
    with TestClient(app) as client:
        video_id = _ready_video(app, settings, tmp_path)
        created = client.post(f"/api/videos/{video_id}/transcription-jobs", json={"language_mode": "ar", "provider": "openai", "approve_estimated_cost": False}).json()
        app.state.worker.process_once()
        waiting = client.get(f"/api/jobs/{created['id']}").json()
        assert waiting["state"] == "awaiting_cost_approval"
        approved = client.post(f"/api/jobs/{created['id']}/approve-cost").json()
        assert approved["state"] == "queued"
        cancelled = client.post(f"/api/jobs/{created['id']}/cancel").json()
        assert cancelled["state"] == "cancelled"


def test_unconfigured_provider_and_invalid_transition(tmp_path: Path) -> None:
    app, settings = _app(tmp_path, FakeProvider(configured=False))
    with TestClient(app) as client:
        video_id = _ready_video(app, settings, tmp_path)
        assert client.post(f"/api/videos/{video_id}/transcription-jobs", json={}).status_code == 503
    job = ProcessingJob(id=str(uuid4()), video_id=str(uuid4()), job_type=JobType.TRANSCRIPTION, state=JobState.QUEUED, progress_percent=0, current_stage="queued", language_mode="auto", transcription_provider="openai", retry_count=0, max_retries=1, cancellation_requested=False, cost_approved=False)
    with pytest.raises(JobTransitionError): transition(job, JobState.COMPLETED, "completed")
