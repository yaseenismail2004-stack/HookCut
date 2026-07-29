from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from openai import APIConnectionError, APITimeoutError, AuthenticationError, BadRequestError, OpenAI, RateLimitError

from hookcut_api.config import Settings

logger = logging.getLogger(__name__)


class ProviderError(ValueError):
    def __init__(self, code: str, message: str, temporary: bool = False) -> None:
        self.code = code
        self.temporary = temporary
        super().__init__(message)


@dataclass(frozen=True)
class TranscriptPart:
    index: int
    start_seconds: float
    end_seconds: float
    text: str
    confidence: float | None = None


@dataclass(frozen=True)
class NormalizedTranscript:
    detected_language: str | None
    language_confidence: float | None
    full_text: str
    duration_seconds: float
    segments: list[TranscriptPart]
    words: list[TranscriptPart]
    provider: str
    model: str
    usage: dict[str, object] | None
    cost_usd: float | None


class TranscriptionProvider(Protocol):
    provider_name: str
    def is_configured(self) -> bool: ...
    def estimate_cost(self, duration_seconds: float) -> float | None: ...
    def transcribe(self, audio_path: Path, language_mode: str) -> NormalizedTranscript: ...


class OpenAITranscriptionProvider:
    provider_name = "openai"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def is_configured(self) -> bool:
        return bool(self._settings.openai_api_key and self._settings.openai_transcription_model)

    def estimate_cost(self, duration_seconds: float) -> float | None:
        rate = self._settings.openai_transcription_cost_per_minute_usd
        return None if rate is None else round(duration_seconds / 60 * rate, 6)

    def transcribe(self, audio_path: Path, language_mode: str) -> NormalizedTranscript:
        if not self.is_configured():
            code = "provider_not_configured" if not self._settings.openai_api_key else "transcription_model_not_configured"
            raise ProviderError(code, "OpenAI transcription is not configured.")
        language = None if language_mode == "auto" else language_mode
        client = OpenAI(api_key=self._settings.openai_api_key, timeout=float(self._settings.openai_request_timeout_seconds), max_retries=0)
        for attempt in range(2):
            try:
                with audio_path.open("rb") as audio_file:
                    model = str(self._settings.openai_transcription_model)
                    if language is None:
                        response = client.audio.transcriptions.create(file=audio_file, model=model, response_format="verbose_json", timestamp_granularities=["segment", "word"])
                    else:
                        response = client.audio.transcriptions.create(file=audio_file, model=model, response_format="verbose_json", timestamp_granularities=["segment", "word"], language=language)
                return self._normalize(response)
            except AuthenticationError as error:
                raise ProviderError("provider_authentication_failed", "The transcription provider rejected authentication.") from error
            except RateLimitError as error:
                if attempt == 0:
                    continue
                raise ProviderError("provider_rate_limited", "The transcription provider is rate limited.", temporary=True) from error
            except (APITimeoutError, APIConnectionError) as error:
                if attempt == 0:
                    continue
                raise ProviderError("provider_timeout", "The transcription provider did not respond in time.", temporary=True) from error
            except BadRequestError as error:
                raise ProviderError("transcription_failed", "The configured model does not accept this transcription request.") from error
        raise ProviderError("transcription_failed", "The transcription provider failed.")

    def _normalize(self, response: object) -> NormalizedTranscript:
        data = response.model_dump() if hasattr(response, "model_dump") else {}
        segments = [TranscriptPart(index=index, start_seconds=float(item.get("start", 0)), end_seconds=float(item.get("end", 0)), text=str(item.get("text", "")), confidence=item.get("confidence")) for index, item in enumerate(data.get("segments") or [])]
        words = [TranscriptPart(index=index, start_seconds=float(item.get("start", 0)), end_seconds=float(item.get("end", 0)), text=str(item.get("word", item.get("text", ""))), confidence=item.get("confidence")) for index, item in enumerate(data.get("words") or [])]
        duration = float(data.get("duration") or (segments[-1].end_seconds if segments else 0))
        return NormalizedTranscript(data.get("language"), data.get("language_probability"), str(data.get("text", "")), duration, segments, words, self.provider_name, str(self._settings.openai_transcription_model), data.get("usage"), None)
