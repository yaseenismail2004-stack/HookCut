from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from hookcut_api.config import Settings
from hookcut_api.db import Base
from hookcut_api.main import create_app
from hookcut_api.models import Transcript, TranscriptSegment, TranscriptStatus, VideoAsset, VideoStatus
from hookcut_api.services.clip_selection import CandidateWindow, LocalSelectionEngine, ProviderCandidate, normalize_comparison_text


class DeterministicClipProvider:
    provider_name = "gemini"
    model_name = "test-only-clip-model"

    def is_configured(self) -> bool: return True
    def estimate_cost(self, candidate_count: int, transcript_seconds: float) -> float | None: return 0.0
    def analyze_candidates(self, candidates: list[CandidateWindow], language: str | None, platform: str) -> list[ProviderCandidate]:
        engine = LocalSelectionEngine()
        return [engine.local_analysis(candidate, platform) for candidate in candidates]


def _app(tmp_path: Path):
    settings = Settings(storage_root=str(tmp_path / "storage"), database_url=f"sqlite:///{(tmp_path / 'selection.db').as_posix()}", worker_enabled=False)
    Base.metadata.create_all(create_engine(settings.resolved_database_url))
    app = create_app(settings)
    app.state.clip_analysis_providers = {"gemini": DeterministicClipProvider()}
    return app, settings


def _ready_transcript(app: object) -> str:
    session = app.state.session_factory()
    video_id, transcript_id, job_id = str(uuid4()), str(uuid4()), str(uuid4())
    session.add(VideoAsset(id=video_id, original_filename="fixture.mp4", stored_filename="fixture.mp4", file_size_bytes=1, container="mp4", duration_seconds=48, width=320, height=240, frame_rate=30, video_codec="h264", audio_codec="aac", audio_channels=1, audio_sample_rate=48000, status=VideoStatus.READY))
    session.add(Transcript(id=transcript_id, video_id=video_id, job_id=job_id, provider="fixture", model="fixture", detected_language="ar", language_confidence=None, full_text="fixture", duration_seconds=48, status=TranscriptStatus.READY))
    texts = ["شلون تتجنب هذا الخطأ الشائع في البداية؟", "أول خطوة هي أن تحدد المشكلة بوضوح.", "لا تبدأ بالتحية لأن المشاهد يريد الفائدة مباشرة.", "بعد ذلك اشرح المثال العملي بشكل مختصر.", "هذه النصيحة توفر وقتاً وتمنع التكرار.", "إذا طبقتها اليوم سترى الفرق بسرعة.", "الخطوة التالية هي مراجعة النتيجة قبل النشر.", "اختم بفكرة كاملة حتى يفهم المشاهد الفائدة.", "يمكنك حفظ هذه النصيحة والعودة إليها لاحقاً.", "هذا مثال هادئ لكنه مفيد للمبتدئين.", "لا تكرر الفكرة نفسها في أكثر من مقطع.", "وهذه نهاية مكتملة للفكرة."]
    for index, text in enumerate(texts): session.add(TranscriptSegment(id=str(uuid4()), transcript_id=transcript_id, segment_index=index, start_seconds=index * 4, end_seconds=(index + 1) * 4, text=text, confidence=None))
    session.commit(); session.close()
    return video_id


def test_segment_only_selection_persists_and_can_be_manually_adjusted(tmp_path: Path) -> None:
    app, _ = _app(tmp_path)
    with TestClient(app) as client:
        video_id = _ready_transcript(app)
        created = client.post(f"/api/videos/{video_id}/clip-selection-jobs", json={"requested_clip_count": 2, "platform": "instagram", "duration_mode": "15_to_30", "selection_mode": "balanced", "diversity_mode": "strict", "approve_estimated_cost": True})
        assert created.status_code == 201
        assert app.state.worker.process_once() is True
        run = client.get(f"/api/videos/{video_id}/clip-selection-runs/latest").json()
        assert run["status"] == "completed"
        candidates = client.get(f"/api/clip-selection-runs/{run['id']}/candidates").json()
        assert candidates and all(item["timestamp_precision"] == "segment" for item in candidates)
        assert all(item["duration_seconds"] <= 30 for item in candidates)
        reserve = next((item for item in candidates if item["selection_status"] == "reserve"), None)
        if reserve:
            assert client.patch(f"/api/clip-candidates/{reserve['id']}/selection", json={"selection_status": "manually_selected"}).status_code in {200, 409}


def test_arabic_normalization_and_duplicate_evidence() -> None:
    assert normalize_comparison_text("إختبارٌ، للاختبار!") == normalize_comparison_text("اختبار للاختبار")
    engine = LocalSelectionEngine()
    first = CandidateWindow("a", 0, 24, "هذه فكرة مفيدة ومكتملة للمشاهد اليوم.", 0, 1, [])
    second = CandidateWindow("b", 4, 28, "هذه فكرة مفيدة ومكتملة للمشاهد اليوم.", 1, 2, [])
    assert engine.duplicate_reason(second, [first]) is not None


def test_local_shortlist_is_compact_diverse_and_records_reserves() -> None:
    engine = LocalSelectionEngine()
    windows = [
        CandidateWindow(f"candidate-{index}", index * 25.0, index * 25.0 + 20.0, f"topic{index} value{index} payoff{index} detail{index} insight{index} lesson{index} result{index}", index, index, ["segment timing only"])
        for index in range(16)
    ]
    shortlist, reasons = engine.shortlist(windows, requested_count=3, max_candidates=12)
    assert len(shortlist) == 12
    assert len({item.id for item in shortlist}) == 12
    assert all(reasons[item.id].startswith("shortlisted:") for item in shortlist)
    assert all(reasons[item.id].startswith("non_analyzed_reserve:") for item in windows if item.id not in {candidate.id for candidate in shortlist})


def test_repeated_selection_runs_use_unique_persisted_candidate_ids(tmp_path: Path) -> None:
    app, _ = _app(tmp_path)
    with TestClient(app) as client:
        video_id = _ready_transcript(app)
        request = {"requested_clip_count": 2, "platform": "instagram", "duration_mode": "15_to_30", "selection_mode": "balanced", "diversity_mode": "strict", "approve_estimated_cost": True}
        for _ in range(2):
            assert client.post(f"/api/videos/{video_id}/clip-selection-jobs", json=request).status_code == 201
            assert app.state.worker.process_once() is True
        session = app.state.session_factory()
        try:
            candidate_ids = session.execute(text("SELECT id FROM clip_candidates")).scalars().all()
        finally:
            session.close()
        assert len(candidate_ids) == len(set(candidate_ids))
