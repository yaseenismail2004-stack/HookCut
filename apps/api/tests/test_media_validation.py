from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from hookcut_api.services import media_validation


def test_ffprobe_timeout_is_a_safe_validation_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def timeout(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd="ffprobe", timeout=20)

    monkeypatch.setattr(media_validation.subprocess, "run", timeout)
    with pytest.raises(media_validation.MediaValidationError, match="timed out") as error:
        media_validation.probe_and_validate(tmp_path / "input.mp4", ".mp4", 7200)
    assert error.value.code == "validation_timeout"


def test_ffprobe_failure_is_not_exposed_as_a_local_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(media_validation.subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args=[], returncode=1))
    with pytest.raises(media_validation.MediaValidationError, match="not readable") as error:
        media_validation.probe_and_validate(tmp_path / "private.mp4", ".mp4", 7200)
    assert error.value.code == "corrupt_media"
    assert str(tmp_path) not in str(error.value)
