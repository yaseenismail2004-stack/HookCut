from __future__ import annotations

import logging
import json
from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Mapping, Protocol

from openai import APIConnectionError, APITimeoutError, AuthenticationError, BadRequestError, OpenAI, RateLimitError

from hookcut_api.config import Settings

logger = logging.getLogger(__name__)


def gemini_sdk_available() -> bool:
    try:
        return find_spec("google.genai") is not None
    except ModuleNotFoundError:
        return False


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

    @property
    def model_name(self) -> str | None: ...

    def is_configured(self) -> bool: ...
    def estimate_cost(self, duration_seconds: float) -> float | None: ...
    def transcribe(self, audio_path: Path, language_mode: str) -> NormalizedTranscript: ...


class OpenAITranscriptionProvider:
    provider_name = "openai"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def model_name(self) -> str | None:
        return self._settings.openai_transcription_model

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


class GeminiTranscriptionProvider:
    """Gemini audio transcription with strict, validated timestamp output."""

    provider_name = "gemini"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def model_name(self) -> str | None:
        return self._settings.gemini_transcription_model

    def is_configured(self) -> bool:
        return bool(self._settings.gemini_api_key and self._settings.gemini_transcription_model and gemini_sdk_available())

    def estimate_cost(self, duration_seconds: float) -> float | None:
        rate = self._settings.gemini_transcription_cost_per_minute_usd
        return None if rate is None else round(duration_seconds / 60 * rate, 6)

    def transcribe(self, audio_path: Path, language_mode: str) -> NormalizedTranscript:
        if not self.is_configured():
            raise ProviderError("provider_not_configured", "Gemini transcription is not configured.")
        prompt = self._prompt(language_mode)
        for attempt in range(2):
            client: Any | None = None
            remote_file: Any | None = None
            request_stage = "client_initialization"
            try:
                client = self._build_client()
                request_stage = "upload"
                remote_file = client.files.upload(file=str(audio_path), config={"mime_type": "audio/flac"})
                remote_uri = getattr(remote_file, "uri", None)
                remote_mime_type = getattr(remote_file, "mime_type", None)
                if not isinstance(remote_uri, str) or not isinstance(remote_mime_type, str):
                    raise ProviderError("provider_response_invalid", "The transcription provider returned an invalid uploaded audio reference.")
                request_stage = "interaction_generate"
                response = client.interactions.create(
                    model=self._settings.gemini_transcription_model,
                    input=[
                        {"type": "text", "text": prompt},
                        {"type": "audio", "uri": remote_uri, "mime_type": remote_mime_type},
                    ],
                    response_format=self._response_format(),
                    store=False,
                )
                request_stage = "normalize"
                normalized = self._normalize(response)
                try:
                    request_stage = "remote_cleanup"
                    self._delete_remote_file(client, remote_file)
                finally:
                    # Do not run a second cleanup attempt after an explicit cleanup
                    # failure: that could hide the original provider-cleanup error.
                    remote_file = None
                return normalized
            except ProviderError:
                raise
            except Exception as error:
                if remote_file is not None and client is not None:
                    self._delete_remote_file(client, remote_file)
                    remote_file = None
                provider_error = self._map_error(error, request_stage)
                if provider_error.temporary and attempt == 0:
                    continue
                raise provider_error from error
            finally:
                if remote_file is not None and client is not None:
                    self._delete_remote_file(client, remote_file)
        raise ProviderError("transcription_failed", "The transcription provider failed.")

    def _build_client(self) -> Any:
        """Create the server-only SDK client; isolated for offline contract tests."""
        try:
            from google import genai
        except ImportError as error:
            raise ProviderError("provider_not_configured", "The Gemini SDK is not installed.") from error
        return genai.Client(
            api_key=str(self._settings.gemini_api_key),
            http_options={"timeout": int(self._settings.gemini_request_timeout_seconds * 1000)},
        )

    def _delete_remote_file(self, client: Any, remote_file: Any) -> None:
        name = getattr(remote_file, "name", None)
        if not name:
            return
        try:
            client.files.delete(name=str(name))
        except Exception as error:
            logger.warning("event=gemini_remote_file_cleanup_failed code=provider_cleanup_failed")
            raise ProviderError("provider_cleanup_failed", "Remote provider audio cleanup could not be confirmed.") from error

    def _normalize(self, response: object) -> NormalizedTranscript:
        text = getattr(response, "output_text", None)
        if not isinstance(text, str):
            raise ProviderError("provider_response_invalid", "The transcription provider returned no structured transcript.")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as error:
            raise ProviderError("provider_response_invalid", "The transcription provider returned invalid transcript data.") from error
        full_text = data.get("full_text")
        raw_segments = data.get("segments")
        if not isinstance(full_text, str) or not full_text.strip() or not isinstance(raw_segments, list) or not raw_segments:
            raise ProviderError("provider_response_invalid", "The transcription provider returned an incomplete transcript.")
        segments: list[TranscriptPart] = []
        previous_end = 0.0
        for index, item in enumerate(raw_segments):
            if not isinstance(item, dict):
                raise ProviderError("provider_response_invalid", "The transcription provider returned an invalid segment.")
            try:
                start = float(item["start_seconds"])
                end = float(item["end_seconds"])
            except (KeyError, TypeError, ValueError) as error:
                raise ProviderError("provider_response_invalid", "The transcription provider did not return usable timestamps.") from error
            segment_text = item.get("text")
            if start < 0 or end <= start or start < previous_end or not isinstance(segment_text, str) or not segment_text.strip():
                raise ProviderError("provider_response_invalid", "The transcription provider returned invalid timestamps.")
            segments.append(TranscriptPart(index=index, start_seconds=start, end_seconds=end, text=segment_text.strip()))
            previous_end = end
        language = data.get("detected_language")
        if language is not None and not isinstance(language, str):
            raise ProviderError("provider_response_invalid", "The transcription provider returned an invalid language value.")
        usage = getattr(response, "usage_metadata", None)
        usage_data = usage.model_dump() if usage is not None and hasattr(usage, "model_dump") else None
        return NormalizedTranscript(language, None, full_text.strip(), segments[-1].end_seconds, segments, [], self.provider_name, self._settings.gemini_transcription_model, usage_data, None)

    @staticmethod
    def _prompt(language_mode: str) -> str:
        requested_language = {"auto": "Automatically detect Arabic, Iraqi Arabic, English, or mixed Arabic-English speech.", "ar": "Transcribe Arabic, including Iraqi Arabic where spoken.", "en": "Transcribe English."}.get(language_mode, "Automatically detect the spoken language.")
        return (
            "Transcribe this audio faithfully. "
            f"{requested_language} "
            "Do not translate, summarize, invent words, or omit meaningful speech. "
            "Return each spoken segment in chronological order with real start_seconds and end_seconds measured from the beginning of the audio. "
            "Use only timestamps supported by the audio; if you cannot determine a timestamp, do not guess."
        )

    @staticmethod
    def _response_format() -> dict[str, object]:
        return {
            "type": "text",
            "mime_type": "application/json",
            "schema": {
                "type": "object",
                "properties": {
                    "detected_language": {"type": "string"},
                    "full_text": {"type": "string"},
                    "segments": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "start_seconds": {"type": "number"},
                                "end_seconds": {"type": "number"},
                                "text": {"type": "string"},
                            },
                            "required": ["start_seconds", "end_seconds", "text"],
                        },
                    },
                },
                "required": ["detected_language", "full_text", "segments"],
            },
        }

    @staticmethod
    def _map_error(error: Exception, stage: str) -> ProviderError:
        status_code = getattr(error, "status_code", None) or getattr(error, "code", None)
        safe_status_code = status_code if isinstance(status_code, int) else None
        logger.warning(
            "event=gemini_provider_request_failed stage=%s error_type=%s status_code=%s",
            stage,
            type(error).__name__,
            safe_status_code,
        )
        if safe_status_code in {401, 403}:
            return ProviderError("provider_authentication_failed", "The transcription provider rejected authentication.")
        if safe_status_code == 429:
            return ProviderError("provider_rate_limited", "The transcription provider is rate limited.", temporary=True)
        if safe_status_code in {408, 504} or "timeout" in type(error).__name__.lower():
            return ProviderError("provider_timeout", "The transcription provider did not respond in time.", temporary=True)
        if safe_status_code == 400:
            return ProviderError("transcription_failed", "The configured model does not accept this transcription request.")
        return ProviderError("transcription_failed", "The transcription provider failed.")


class TranscriptionProviderRegistry:
    """Provider lookup with no automatic cross-provider fallback or spending."""

    def __init__(self, providers: Mapping[str, TranscriptionProvider]) -> None:
        self._providers = dict(providers)

    def get(self, name: str) -> TranscriptionProvider | None:
        return self._providers.get(name)

    def configured_names(self) -> list[str]:
        return [name for name, provider in self._providers.items() if provider.is_configured()]


def build_provider_registry(settings: Settings) -> TranscriptionProviderRegistry:
    return TranscriptionProviderRegistry({
        "gemini": GeminiTranscriptionProvider(settings),
        "openai": OpenAITranscriptionProvider(settings),
    })
