from __future__ import annotations

import json
import logging
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)


class AudioExtractionError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class AudioMetadata:
    duration_seconds: float
    codec: str
    sample_rate: int
    channels: int
    file_size_bytes: int


def probe_audio(path: Path) -> AudioMetadata:
    try:
        result = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)], capture_output=True, text=True, timeout=20, check=False)
    except subprocess.TimeoutExpired as error:
        raise AudioExtractionError("validation_timeout", "Audio validation timed out.") from error
    if result.returncode != 0:
        raise AudioExtractionError("audio_extraction_failed", "Extracted audio could not be validated.")
    try:
        payload = json.loads(result.stdout)
        stream = next(item for item in payload["streams"] if item.get("codec_type") == "audio" and int(item.get("channels") or 0) > 0)
        metadata = AudioMetadata(float(payload["format"]["duration"]), str(stream["codec_name"]), int(stream["sample_rate"]), int(stream["channels"]), path.stat().st_size)
    except (KeyError, StopIteration, TypeError, ValueError, json.JSONDecodeError) as error:
        raise AudioExtractionError("audio_extraction_failed", "Extracted audio metadata is invalid.") from error
    if metadata.file_size_bytes <= 0 or metadata.duration_seconds <= 0:
        raise AudioExtractionError("audio_extraction_failed", "Extracted audio is empty.")
    return metadata


def extract_audio(source: Path, destination: Path, source_duration: float, on_progress: Callable[[float], None], is_cancelled: Callable[[], bool], timeout_seconds: int = 600) -> AudioMetadata:
    """Create a real normalized FLAC file using FFmpeg without shell interpolation."""
    command = ["ffmpeg", "-y", "-v", "error", "-i", str(source), "-vn", "-map", "0:a:0", "-ac", "1", "-ar", "16000", "-c:a", "flac", "-progress", "pipe:1", "-nostats", str(destination)]
    logger.info("event=audio_extraction_started")
    started = time.monotonic()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace")
    try:
        assert process.stdout is not None
        for line in process.stdout:
            if is_cancelled():
                process.terminate()
                raise AudioExtractionError("job_cancelled", "Audio extraction was cancelled.")
            if time.monotonic() - started > timeout_seconds:
                process.kill()
                raise AudioExtractionError("audio_extraction_timeout", "Audio extraction timed out.")
            key, separator, value = line.strip().partition("=")
            if separator and key == "out_time_ms" and source_duration > 0:
                on_progress(min(99.0, max(0.0, float(value) / 1_000_000 / source_duration * 100)))
        if process.wait(timeout=10) != 0:
            raise AudioExtractionError("audio_extraction_failed", "Audio extraction failed.")
        on_progress(100.0)
        metadata = probe_audio(destination)
        logger.info("event=audio_extraction_completed duration_seconds=%.3f", metadata.duration_seconds)
        return metadata
    except (OSError, subprocess.SubprocessError) as error:
        raise AudioExtractionError("audio_extraction_failed", "Audio extraction failed.") from error
    finally:
        if process.poll() is None:
            process.kill()
