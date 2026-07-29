from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm"}
CONTAINERS_BY_EXTENSION = {
    ".mp4": {"mov,mp4,m4a,3gp,3g2,mj2"},
    ".mov": {"mov,mp4,m4a,3gp,3g2,mj2"},
    ".mkv": {"matroska,webm"},
    ".webm": {"matroska,webm"},
}


class MediaValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class MediaMetadata:
    container: str
    duration_seconds: float
    width: int
    height: int
    frame_rate: float
    video_codec: str
    audio_codec: str
    audio_channels: int
    audio_sample_rate: int


def _frame_rate(value: str) -> float:
    numerator, denominator = value.split("/", maxsplit=1)
    if float(denominator) == 0:
        raise ValueError
    return round(float(numerator) / float(denominator), 3)


def probe_and_validate(path: Path, extension: str, max_duration_seconds: int, max_resolution: int = 3840) -> MediaMetadata:
    try:
        logger.info("event=ffprobe_started")
        completed = subprocess.run(
            ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except subprocess.TimeoutExpired as error:
        logger.warning("event=ffprobe_timed_out")
        raise MediaValidationError("validation_timeout", "Media validation timed out.") from error
    except OSError as error:
        logger.exception("event=ffprobe_unavailable")
        raise MediaValidationError("storage_error", "Media validator is unavailable.") from error
    logger.info("event=ffprobe_completed return_code=%s", completed.returncode)
    if completed.returncode != 0:
        logger.warning("event=ffprobe_failed return_code=%s", completed.returncode)
        raise MediaValidationError("corrupt_media", "The uploaded file is not readable media.")
    try:
        payload = json.loads(completed.stdout)
        format_info = payload["format"]
        container = str(format_info["format_name"])
        duration = float(format_info["duration"])
        streams = payload["streams"]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise MediaValidationError("corrupt_media", "The uploaded file has missing or invalid media metadata.") from error

    video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]
    if not video_streams:
        raise MediaValidationError("missing_video_stream", "The video stream is missing.")
    audio_streams = [
        stream for stream in streams if stream.get("codec_type") == "audio" and int(stream.get("channels") or 0) > 0
    ]
    if not audio_streams:
        raise MediaValidationError("missing_audio_stream", "A usable audio stream is missing.")
    try:
        video = video_streams[0]
        audio = audio_streams[0]
        metadata = MediaMetadata(
            container=container,
            duration_seconds=duration,
            width=int(video["width"]),
            height=int(video["height"]),
            frame_rate=_frame_rate(str(video.get("avg_frame_rate") or video["r_frame_rate"])),
            video_codec=str(video["codec_name"]),
            audio_codec=str(audio["codec_name"]),
            audio_channels=int(audio["channels"]),
            audio_sample_rate=int(audio["sample_rate"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise MediaValidationError("corrupt_media", "The uploaded file has missing or invalid media metadata.") from error
    if metadata.container not in CONTAINERS_BY_EXTENSION[extension]:
        raise MediaValidationError("unsupported_format", "The file container does not match its extension.")
    if metadata.duration_seconds < 20:
        raise MediaValidationError("video_too_short", "Video must be at least 20 seconds long.")
    if metadata.duration_seconds > max_duration_seconds:
        raise MediaValidationError("video_too_long", "Video exceeds the maximum permitted duration.")
    if metadata.width > max_resolution or metadata.height > max_resolution:
        raise MediaValidationError("resolution_too_high", "Video resolution exceeds 4K.")
    return metadata
