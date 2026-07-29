from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from hookcut_api.config import Settings
from hookcut_api.db import Base
from hookcut_api.main import create_app
from hookcut_api.services.media_validation import MediaMetadata


def _client(tmp_path: Path) -> TestClient:
    database = tmp_path / "video-test.db"
    settings = Settings(storage_root=str(tmp_path / "storage"), database_url=f"sqlite:///{database.as_posix()}")
    engine = create_engine(settings.resolved_database_url)
    Base.metadata.create_all(engine)
    return TestClient(create_app(settings))


def _metadata() -> MediaMetadata:
    return MediaMetadata("mov,mp4,m4a,3gp,3g2,mj2", 21.0, 320, 240, 30.0, "h264", "aac", 2, 48000)


def test_upload_metadata_list_get_and_repeatable_delete(tmp_path: Path, monkeypatch: object) -> None:
    monkeypatch.setattr("hookcut_api.routers.videos.probe_and_validate", lambda *args: _metadata())  # type: ignore[attr-defined]
    with _client(tmp_path) as client:
        upload = client.post("/api/videos/upload", files={"file": ("display.mp4", b"not-a-real-file", "video/mp4")})
        assert upload.status_code == 201
        payload = upload.json()
        assert payload["original_filename"] == "display.mp4"
        assert "stored_filename" not in payload and str(tmp_path) not in upload.text
        video_id = payload["id"]
        assert client.get("/api/videos").json()[0]["id"] == video_id
        assert client.get(f"/api/videos/{video_id}").status_code == 200
        upload_root = tmp_path / "storage" / "uploads"
        stored = list(upload_root.iterdir())
        assert len(stored) == 1 and stored[0].name != "display.mp4"
        assert client.delete(f"/api/videos/{video_id}").json()["already_deleted"] is False
        assert not stored[0].exists()
        assert client.delete(f"/api/videos/{video_id}").json()["already_deleted"] is True


def test_upload_rejects_unsupported_and_misleading_format(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        bad_extension = client.post("/api/videos/upload", files={"file": ("demo.txt", b"x", "video/mp4")})
        bad_type = client.post("/api/videos/upload", files={"file": ("demo.mp4", b"x", "text/plain")})
    assert bad_extension.status_code == 415 and bad_extension.json()["detail"]["code"] == "unsupported_format"
    assert bad_type.status_code == 415 and bad_type.json()["detail"]["code"] == "unsupported_format"
