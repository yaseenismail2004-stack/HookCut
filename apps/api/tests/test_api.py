from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

from hookcut_api.config import Settings
from hookcut_api.main import create_app


def test_health_endpoint_returns_real_service_metadata(tmp_path: Path) -> None:
    settings = Settings(storage_root=str(tmp_path))
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "hookcut-api", "version": "0.1.0"}


def test_capabilities_never_return_secret_values(tmp_path: Path) -> None:
    secret = "do-not-return-this-secret"
    settings = Settings(storage_root=str(tmp_path), openai_api_key=secret, database_url="sqlite:///private.db")
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/system/capabilities")
    assert response.status_code == 200
    payload = response.json()
    assert payload["configuration"]["openai_api_key_configured"] is True
    assert payload["configuration"]["database_configured"] is True
    assert secret not in response.text
    assert "private.db" not in response.text
    assert "storage_root" not in response.text


def test_invalid_configuration_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(max_upload_size_mb=0)
