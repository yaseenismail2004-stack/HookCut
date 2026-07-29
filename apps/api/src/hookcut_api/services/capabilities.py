from __future__ import annotations

import shutil
import subprocess
import sys
from importlib.util import find_spec

from hookcut_api.config import Settings
from hookcut_api.schemas import (
    CapabilitiesResponse,
    ConfigurationState,
    StorageCapabilities,
    ToolAvailability,
)
from hookcut_api.services.storage import StorageService


def _tool_availability(command: str) -> ToolAvailability:
    executable = shutil.which(command)
    if executable is None:
        return ToolAvailability(available=False)
    try:
        completed = subprocess.run(
            [executable, "-version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return ToolAvailability(available=False)
    first_line = completed.stdout.splitlines()[0] if completed.returncode == 0 and completed.stdout else None
    return ToolAvailability(available=completed.returncode == 0, version=first_line)


def detect_capabilities(settings: Settings, storage: StorageService, worker_running: bool = False) -> CapabilitiesResponse:
    """Report only safe boolean/version capability information, never local paths or secrets."""

    return CapabilitiesResponse(
        python=ToolAvailability(available=True, version=sys.version.split()[0]),
        ffmpeg=_tool_availability("ffmpeg"),
        ffprobe=_tool_availability("ffprobe"),
        storage=StorageCapabilities(
            directories_ready=storage.directories_ready(),
            project_write_permission=storage.project_write_permission(),
        ),
        configuration=ConfigurationState(
            openai_api_key_configured=bool(settings.openai_api_key),
            openai_sdk_available=find_spec("openai") is not None,
            transcription_model_configured=bool(settings.openai_transcription_model),
            transcription_provider_available=bool(settings.openai_api_key and settings.openai_transcription_model),
            cost_estimation_configured=settings.openai_transcription_cost_per_minute_usd is not None,
            database_configured=bool(settings.database_url),
        ),
        worker_running=worker_running,
    )
