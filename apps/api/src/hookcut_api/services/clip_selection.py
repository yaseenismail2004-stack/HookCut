from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from importlib.util import find_spec
from typing import Any, Literal, Mapping, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from hookcut_api.config import Settings
from hookcut_api.services.transcription import ProviderError

logger = logging.getLogger(__name__)

PLATFORMS = {"instagram", "tiktok", "youtube"}
DURATION_MODES = {"auto", "15_to_30", "30_to_60", "45_to_90"}
SELECTION_MODES = {"highest_potential", "balanced", "exact_count"}
DIVERSITY_MODES = {"strict", "balanced", "similar_allowed"}
GREETINGS = {"hello", "hi", "hey", "هلا", "اهلا", "مرحبا", "السلام عليكم"}
FILLER = {"um", "uh", "يعني", "ااا", "امم"}


def duration_limits(mode: str) -> tuple[float, float]:
    return {"auto": (20.0, 90.0), "15_to_30": (15.0, 30.0), "30_to_60": (30.0, 60.0), "45_to_90": (45.0, 90.0)}[mode]


def normalize_comparison_text(text: str) -> str:
    text = re.sub(r"[\u0610-\u061a\u064b-\u065f\u0670]", "", text)
    text = re.sub(r"[إأآا]", "ا", text)
    text = text.replace("ى", "ي").replace("ة", "ه")
    text = re.sub(r"[^\w\s]", " ", text.lower(), flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def token_overlap(left: str, right: str) -> float:
    a, b = set(normalize_comparison_text(left).split()), set(normalize_comparison_text(right).split())
    return len(a & b) / len(a | b) if a and b else 0.0


def timeline_iou(start_a: float, end_a: float, start_b: float, end_b: float) -> float:
    intersection = max(0.0, min(end_a, end_b) - max(start_a, start_b))
    union = max(end_a, end_b) - min(start_a, start_b)
    return intersection / union if union else 0.0


@dataclass(frozen=True)
class SegmentEvidence:
    index: int
    start_seconds: float
    end_seconds: float
    text: str
    confidence: float | None = None


@dataclass(frozen=True)
class CandidateWindow:
    id: str
    start_seconds: float
    end_seconds: float
    transcript_text: str
    segment_start: int
    segment_end: int
    boundary_notes: list[str]

    @property
    def duration_seconds(self) -> float:
        return round(self.end_seconds - self.start_seconds, 3)


class ProviderCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_id: str
    start_time: float = Field(ge=0)
    end_time: float = Field(gt=0)
    duration: float = Field(gt=0, le=90)
    timestamp_precision: Literal["segment", "word"]
    transcript: str = Field(min_length=1)
    topic: str = Field(min_length=1, max_length=256)
    summary: str = Field(min_length=1)
    hook_type: str = Field(min_length=1, max_length=64)
    hook_text: str = Field(min_length=1)
    hook_score: float = Field(ge=0, le=100)
    hook_reason: str = Field(min_length=1)
    first_1_second_score: float = Field(ge=0, le=100)
    first_3_seconds_score: float = Field(ge=0, le=100)
    first_5_seconds_score: float = Field(ge=0, le=100)
    retention_score: float = Field(ge=0, le=100)
    retention_reason: str = Field(min_length=1)
    standalone_score: float = Field(ge=0, le=100)
    usefulness_score: float = Field(ge=0, le=100)
    entertainment_score: float = Field(ge=0, le=100)
    emotional_impact_score: float = Field(ge=0, le=100)
    share_potential_score: float = Field(ge=0, le=100)
    save_potential_score: float = Field(ge=0, le=100)
    comment_potential_score: float = Field(ge=0, le=100)
    loop_potential_score: float = Field(ge=0, le=100)
    visual_suitability_score: float = Field(ge=0, le=100)
    viral_potential_score: float = Field(ge=0, le=100)
    confidence_score: float = Field(ge=0, le=100)
    ideal_platform: str
    target_audience: str = Field(min_length=1, max_length=256)
    likely_viewer_reaction: str = Field(min_length=1, max_length=256)
    suggested_title: str = Field(min_length=1, max_length=256)
    suggested_on_screen_hook: str = Field(min_length=1, max_length=256)
    detected_weaknesses: list[str] = Field(default_factory=list)
    selection_status: Literal["selected", "reserve", "rejected"]
    selection_reason: str = Field(min_length=1)
    rejection_reason: str | None = None
    similarity_group: str | None = None

    @field_validator("ideal_platform")
    @classmethod
    def platform_is_allowed(cls, value: str) -> str:
        if value not in PLATFORMS:
            raise ValueError("Unsupported ideal platform.")
        return value

    @model_validator(mode="after")
    def timestamps_are_consistent(self) -> "ProviderCandidate":
        if self.end_time <= self.start_time or abs((self.end_time - self.start_time) - self.duration) > 0.05:
            raise ValueError("Provider timing is inconsistent.")
        expected_viral_score = self.calculated_viral_potential_score
        if abs(self.viral_potential_score - expected_viral_score) > 0.5:
            raise ValueError("Provider viral-potential score does not match the required weighted components.")
        return self

    @property
    def calculated_viral_potential_score(self) -> float:
        return round(
            self.hook_score * .20 + self.retention_score * .20 + self.standalone_score * .12
            + max(self.usefulness_score, self.entertainment_score) * .12 + self.emotional_impact_score * .10
            + self.share_potential_score * .08 + self.save_potential_score * .05 + self.comment_potential_score * .05
            + self.loop_potential_score * .05 + self.visual_suitability_score * .03, 2,
        )


HOOK_TYPES = {
    "direct_question", "surprising_claim", "warning", "common_mistake", "bold_opinion",
    "controversy", "transformation", "confession", "curiosity_gap", "unexpected_result",
    "useful_promise", "numbered_advice", "problem_first", "myth_vs_reality", "before_after",
    "emotional_statement", "other",
}
WEAKNESS_CODES = {
    "slow_start", "greeting", "filler", "missing_context", "delayed_payoff", "weak_ending",
    "repetitive", "low_specificity", "unclear_reference", "low_emotion", "low_value",
    "platform_mismatch", "none",
}


class UltraFlatProviderAnalysis(BaseModel):
    """Semantic fields only; all source evidence and selection decisions remain local."""

    model_config = ConfigDict(extra="forbid")
    candidate_id: str = Field(min_length=1)
    topic: str = Field(min_length=1, max_length=60)
    hook_type: str
    hook_score: float = Field(ge=0, le=100)
    first_1_second_score: float = Field(ge=0, le=100)
    first_3_seconds_score: float = Field(ge=0, le=100)
    first_5_seconds_score: float = Field(ge=0, le=100)
    retention_score: float = Field(ge=0, le=100)
    standalone_score: float = Field(ge=0, le=100)
    usefulness_score: float = Field(ge=0, le=100)
    entertainment_score: float = Field(ge=0, le=100)
    emotional_score: float = Field(ge=0, le=100)
    share_score: float = Field(ge=0, le=100)
    save_score: float = Field(ge=0, le=100)
    comment_score: float = Field(ge=0, le=100)
    loop_score: float = Field(ge=0, le=100)
    visual_score: float = Field(ge=0, le=100)
    confidence_score: float = Field(ge=0, le=100)
    suggested_title: str = Field(min_length=1, max_length=100)
    suggested_hook: str = Field(min_length=1, max_length=120)
    weakness_codes: list[str] = Field(max_length=4)
    analysis_note: str = Field(min_length=1, max_length=180)

    @field_validator("hook_type")
    @classmethod
    def hook_type_is_allowed(cls, value: str) -> str:
        if value not in HOOK_TYPES:
            raise ValueError("Unsupported hook type.")
        return value

    @field_validator("weakness_codes")
    @classmethod
    def weakness_codes_are_allowed(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)) or any(value not in WEAKNESS_CODES for value in values):
            raise ValueError("Unsupported or duplicate weakness code.")
        return values


class UltraFlatClipAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    analyses: list[UltraFlatProviderAnalysis]


# Compatibility name for internal callers; it now represents the ultra-flat contract.
CompactClipAnalysisResponse = UltraFlatClipAnalysisResponse


def calculate_viral_potential(hook_score: float, retention_score: float, standalone_score: float,
                              usefulness_score: float, entertainment_score: float, emotional_score: float,
                              share_score: float, save_score: float, comment_score: float, loop_score: float,
                              visual_score: float) -> float:
    return round(hook_score * .20 + retention_score * .20 + standalone_score * .12
                 + max(usefulness_score, entertainment_score) * .12 + emotional_score * .10
                 + share_score * .08 + save_score * .05 + comment_score * .05 + loop_score * .05
                 + visual_score * .03, 2)


def ultra_flat_response_json_schema(model_name: str | None = None) -> dict[str, object]:
    """Minimal provider schema: no references, unions, nullable values, or nested semantic objects."""
    score_fields = {
        "hook_score", "first_1_second_score", "first_3_seconds_score", "first_5_seconds_score",
        "retention_score", "standalone_score", "usefulness_score", "entertainment_score",
        "emotional_score", "share_score", "save_score", "comment_score", "loop_score",
        "visual_score", "confidence_score",
    }
    ordered_fields = [
        "candidate_id", "topic", "hook_type", "hook_score", "first_1_second_score",
        "first_3_seconds_score", "first_5_seconds_score", "retention_score", "standalone_score",
        "usefulness_score", "entertainment_score", "emotional_score", "share_score", "save_score",
        "comment_score", "loop_score", "visual_score", "confidence_score", "suggested_title",
        "suggested_hook", "weakness_codes", "analysis_note",
    ]
    properties: dict[str, object] = {}
    for field in ordered_fields:
        if field in score_fields:
            properties[field] = {"type": "number"}
        elif field == "hook_type":
            properties[field] = {"type": "string", "enum": sorted(HOOK_TYPES)}
        elif field == "weakness_codes":
            properties[field] = {"type": "array", "items": {"type": "string", "enum": sorted(WEAKNESS_CODES)}}
        else:
            properties[field] = {"type": "string"}
    analysis_schema: dict[str, object] = {"type": "object", "properties": properties, "required": ordered_fields}
    if model_name and model_name.lower().startswith("gemini-2.0"):
        analysis_schema["propertyOrdering"] = ordered_fields
    return {
        "type": "object",
        "properties": {"analyses": {"type": "array", "items": analysis_schema}},
        "required": ["analyses"],
    }


def generate_content_config(settings: Settings, model_name: str | None) -> Any:
    """Build the SDK config locally so tests can verify the raw-schema transport without a network call."""
    from google.genai import types

    return types.GenerateContentConfig(
        response_mime_type="application/json",
        response_json_schema=ultra_flat_response_json_schema(model_name),
        temperature=0.1,
        max_output_tokens=settings.gemini_clip_analysis_max_output_tokens,
    )


def schema_metrics(schema: Mapping[str, object]) -> dict[str, object]:
    """Return structural schema metrics only, suitable for documentation and safe diagnostics."""
    serialized = json.dumps(schema, sort_keys=True, separators=(",", ":"))
    counts = {"properties": 0, "required": 0, "defs": 0, "refs": 0}

    def walk(value: object, depth: int = 0) -> int:
        if not isinstance(value, Mapping):
            return depth
        properties = value.get("properties")
        if isinstance(properties, Mapping):
            counts["properties"] += len(properties)
        required = value.get("required")
        if isinstance(required, list):
            counts["required"] += len(required)
        definitions = value.get("$defs")
        if isinstance(definitions, Mapping):
            counts["defs"] += len(definitions)
        counts["refs"] += 1 if "$ref" in value else 0
        node_type = value.get("type")
        structural_depth = depth + 1 if isinstance(node_type, str) and node_type in {"object", "array"} else depth
        maximum = structural_depth
        if isinstance(properties, Mapping):
            for item in properties.values():
                maximum = max(maximum, walk(item, structural_depth))
        item_schema = value.get("items")
        if isinstance(item_schema, Mapping):
            maximum = max(maximum, walk(item_schema, structural_depth))
        if isinstance(definitions, Mapping):
            for item in definitions.values():
                maximum = max(maximum, walk(item, depth))
        return maximum

    return {
        "character_count": len(serialized), "maximum_nesting_depth": walk(schema),
        "property_count": counts["properties"], "required_property_count": counts["required"],
        "$defs_count": counts["defs"], "$ref_count": counts["refs"],
        "has_anyOf": "anyOf" in serialized, "has_oneOf": "oneOf" in serialized,
        "has_allOf": "allOf" in serialized, "has_null_type": '"null"' in serialized,
        "has_additionalProperties": "additionalProperties" in serialized,
        "has_defaults": '"default"' in serialized,
    }


def _structure(value: object, depth: int = 0) -> object:
    """Shape-only recursion: no semantic response values are returned or logged."""
    if depth >= 2:
        return type(value).__name__
    if isinstance(value, Mapping):
        return {"type": "object", "fields": {str(key): _structure(item, depth + 1) for key, item in list(value.items())[:40]}}
    if isinstance(value, list):
        return {"type": "array", "length": len(value), "item": _structure(value[0], depth + 1) if value else None}
    return type(value).__name__


def _safe_response_text(value: object) -> str | None:
    try:
        text = value if isinstance(value, str) else getattr(value, "text", None)
    except Exception:
        return None
    return text if isinstance(text, str) else None


def provider_structural_diagnostics(
    value: object | None, error: Exception | None = None, *, settings: Settings | None = None,
    shortlist_count: int | None = None, transcript_characters: int | None = None,
) -> dict[str, object]:
    """Return structural diagnostics only; semantic output and request evidence never leave memory."""
    import hashlib

    try:
        parsed = getattr(value, "parsed", None) if value is not None else None
    except Exception:
        parsed = None
    response_text = _safe_response_text(value) if value is not None else None
    if parsed is not None:
        source, shape = "response_parsed", _structure(parsed)
    elif isinstance(response_text, str):
        source = "response_text"
        try:
            shape = _structure(json.loads(response_text))
        except json.JSONDecodeError:
            shape = {"type": "invalid_json_text"}
    elif isinstance(value, (Mapping, list, BaseModel)):
        source, shape = "safe_parsed_value", _structure(value.model_dump() if isinstance(value, BaseModel) else value)
    else:
        source, shape = "generate_content_response", {"type": type(value).__name__ if value is not None else "NoneType"}
    response_candidates = getattr(value, "candidates", None) if value is not None else None
    finish_reasons = [str(getattr(item, "finish_reason", "")) for item in response_candidates] if isinstance(response_candidates, list) else []
    prompt_feedback = getattr(value, "prompt_feedback", None) if value is not None else None
    block_reason = str(getattr(prompt_feedback, "block_reason", "")) if prompt_feedback is not None else None
    usage = getattr(value, "usage_metadata", None) if value is not None else None
    diagnostics: dict[str, object] = {
        "parsing_source": source,
        "response_returned": value is not None,
        "parsed_present": parsed is not None,
        "parsed_type": type(parsed).__name__ if parsed is not None else None,
        "text_present": isinstance(response_text, str),
        "response_character_count": len(response_text) if isinstance(response_text, str) else None,
        "response_hash": hashlib.sha256(response_text.encode("utf-8")).hexdigest() if isinstance(response_text, str) else None,
        "shape": shape,
        "validation_paths": [],
        "finish_reasons": finish_reasons,
        "prompt_block_reason": block_reason or None,
        "usage_metadata_present": usage is not None,
        "prompt_token_count": getattr(usage, "prompt_token_count", None) if usage is not None else None,
        "output_token_count": getattr(usage, "candidates_token_count", None) if usage is not None else None,
        "configured_max_output_tokens": settings.gemini_clip_analysis_max_output_tokens if settings else None,
        "submitted_shortlist_count": shortlist_count,
        "submitted_transcript_characters": transcript_characters,
        "exception_class": type(error).__name__ if error else None,
        "exception_status": getattr(error, "status_code", None) if error else None,
    }
    if isinstance(error, ValidationError):
        diagnostics["validation_paths"] = [".".join(str(part) for part in issue["loc"]) for issue in error.errors()]
    return diagnostics


def _compact_response_from_parsed(value: object) -> UltraFlatClipAnalysisResponse:
    if isinstance(value, UltraFlatClipAnalysisResponse):
        return value
    if isinstance(value, BaseModel):
        value = value.model_dump()
    if isinstance(value, Mapping):
        normalized = {str(key): item for key, item in value.items()}
        value = normalized
    if isinstance(value, Mapping):
        return UltraFlatClipAnalysisResponse.model_validate(value)
    raise ValueError("Generate Content returned no supported parsed result.")


def _validate_semantic_limits(analysis: UltraFlatProviderAnalysis, settings: Settings) -> None:
    if len(analysis.topic) > settings.gemini_clip_analysis_max_topic_chars:
        raise ValueError("Provider topic exceeds the configured compact limit.")
    if len(analysis.suggested_title) > settings.gemini_clip_analysis_max_title_chars:
        raise ValueError("Provider title exceeds the configured compact limit.")
    if len(analysis.suggested_hook) > settings.gemini_clip_analysis_max_hook_chars:
        raise ValueError("Provider hook exceeds the configured compact limit.")
    if len(analysis.analysis_note) > settings.gemini_clip_analysis_max_analysis_note_chars:
        raise ValueError("Provider analysis note exceeds the configured compact limit.")
    if len(analysis.weakness_codes) > settings.gemini_clip_analysis_max_detected_weaknesses:
        raise ValueError("Provider returned too many weaknesses.")


def join_provider_analysis(analysis: UltraFlatProviderAnalysis, candidate: CandidateWindow, platform: str) -> ProviderCandidate:
    """Create the canonical persistence object from local evidence plus validated semantics."""
    return ProviderCandidate(
        candidate_id=candidate.id, start_time=candidate.start_seconds, end_time=candidate.end_seconds,
        duration=candidate.duration_seconds, timestamp_precision="segment", transcript=candidate.transcript_text,
        topic=analysis.topic, summary=analysis.analysis_note, hook_type=analysis.hook_type,
        hook_text=analysis.suggested_hook, hook_score=analysis.hook_score,
        hook_reason=analysis.analysis_note, first_1_second_score=analysis.first_1_second_score,
        first_3_seconds_score=analysis.first_3_seconds_score,
        first_5_seconds_score=analysis.first_5_seconds_score, retention_score=analysis.retention_score,
        retention_reason=analysis.analysis_note, standalone_score=analysis.standalone_score,
        usefulness_score=analysis.usefulness_score, entertainment_score=analysis.entertainment_score,
        emotional_impact_score=analysis.emotional_score, share_potential_score=analysis.share_score,
        save_potential_score=analysis.save_score, comment_potential_score=analysis.comment_score,
        loop_potential_score=analysis.loop_score, visual_suitability_score=analysis.visual_score,
        viral_potential_score=calculate_viral_potential(analysis.hook_score, analysis.retention_score, analysis.standalone_score,
            analysis.usefulness_score, analysis.entertainment_score, analysis.emotional_score, analysis.share_score,
            analysis.save_score, analysis.comment_score, analysis.loop_score, analysis.visual_score),
        confidence_score=analysis.confidence_score, ideal_platform=platform,
        target_audience="Not assessed by the ultra-flat provider contract.",
        likely_viewer_reaction="Not assessed by the ultra-flat provider contract.", suggested_title=analysis.suggested_title,
        suggested_on_screen_hook=analysis.suggested_hook, detected_weaknesses=analysis.weakness_codes,
        selection_status="reserve", selection_reason="Semantic provider analysis joined to canonical local evidence.",
    )


def normalize_provider_response(raw: object, candidates: list[CandidateWindow], settings: Settings, platform: str = "instagram") -> list[ProviderCandidate]:
    """Validate Generate Content parsed data, then join it to canonical local evidence."""
    response = _compact_response_from_parsed(raw)
    candidate_by_id = {candidate.id: candidate for candidate in candidates}
    ids = [item.candidate_id for item in response.analyses]
    if len(ids) != len(set(ids)) or set(ids) != set(candidate_by_id):
        raise ValueError("Provider candidate IDs do not match the requested shortlist.")
    canonical: list[ProviderCandidate] = []
    for item in response.analyses:
        candidate = candidate_by_id[item.candidate_id]
        _validate_semantic_limits(item, settings)
        canonical.append(join_provider_analysis(item, candidate, platform))
    return canonical


def parse_generate_content_response(response: object, candidates: list[CandidateWindow], settings: Settings, platform: str = "instagram") -> list[ProviderCandidate]:
    """Prefer the SDK parsed object; use JSON text only when parsed output is absent."""
    parsed = getattr(response, "parsed", None)
    if parsed is not None:
        return normalize_provider_response(parsed, candidates, settings, platform)
    text = _safe_response_text(response)
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Generate Content returned neither parsed output nor JSON text.")
    compact = UltraFlatClipAnalysisResponse.model_validate_json(text)
    return normalize_provider_response(compact, candidates, settings, platform)


def generate_content_response_error(response: object) -> ProviderError | None:
    """Map safe completion signals without recording generated text."""
    candidates = getattr(response, "candidates", None)
    first = candidates[0] if isinstance(candidates, list) and candidates else None
    reason = str(getattr(first, "finish_reason", "")).lower()
    if "max" in reason or "token" in reason:
        return ProviderError("provider_output_truncated", "Gemini output reached the configured token limit.")
    if "safety" in reason or "block" in reason:
        return ProviderError("provider_content_blocked", "Gemini blocked the clip-analysis response.")
    prompt_feedback = getattr(response, "prompt_feedback", None)
    block_reason = str(getattr(prompt_feedback, "block_reason", "")).lower() if prompt_feedback is not None else ""
    if "safety" in block_reason or "block" in block_reason:
        return ProviderError("provider_content_blocked", "Gemini blocked the clip-analysis response.")
    return None


class ClipAnalysisProvider(Protocol):
    provider_name: str

    @property
    def model_name(self) -> str | None: ...
    def is_configured(self) -> bool: ...
    def estimate_cost(self, candidate_count: int, transcript_seconds: float) -> float | None: ...
    def analyze_candidates(self, candidates: list[CandidateWindow], language: str | None, platform: str) -> list[ProviderCandidate]: ...


def compact_provider_payload(candidates: list[CandidateWindow], settings: Settings) -> tuple[list[dict[str, object]], dict[str, int]]:
    """Build the smallest provider payload without timestamps or canonical source data."""
    if len(candidates) > settings.gemini_clip_analysis_max_candidates_per_request:
        raise ProviderError("provider_shortlist_too_large", "The compact provider shortlist exceeds the configured request limit.")
    payload: list[dict[str, object]] = []
    transcript_characters = 0
    for candidate in candidates:
        transcript = _compact_evidence(candidate.transcript_text, settings.gemini_clip_analysis_max_transcript_chars_per_candidate)
        payload.append({"candidate_id": candidate.id, "transcript_excerpt": transcript, "relative_duration_seconds": candidate.duration_seconds})
        transcript_characters += len(transcript)
    # Flat analysis contains 22 compact fields. Two characters per token is deliberately conservative
    # for multilingual JSON; the configured output limit must remain above this preflight estimate.
    expected_response_characters = len(candidates) * 700 + 500
    expected_response_tokens = (expected_response_characters + 1) // 2
    request_characters = transcript_characters + 1000
    if request_characters > settings.gemini_clip_analysis_max_request_chars:
        raise ProviderError("provider_context_budget_exceeded", "The compact provider request exceeds the configured safe input budget.")
    if expected_response_characters > settings.gemini_clip_analysis_max_expected_response_chars:
        raise ProviderError("provider_response_budget_exceeded", "The compact provider response estimate exceeds the configured safe output budget.")
    if expected_response_tokens >= settings.gemini_clip_analysis_max_output_tokens:
        raise ProviderError("provider_output_budget_exceeded", "The configured output-token limit is below the conservative compact response budget.")
    return payload, {
        "input_characters": request_characters,
        "expected_response_characters": expected_response_characters,
        "expected_response_tokens": expected_response_tokens,
    }


def _compact_evidence(value: str, limit: int) -> str:
    """Keep bounded provider evidence at a Unicode whitespace boundary; never split a word or code point."""
    transcript = value.strip()
    if len(transcript) <= limit:
        return transcript
    boundary = max(transcript.rfind(" ", 0, limit + 1), transcript.rfind("\n", 0, limit + 1), transcript.rfind("\t", 0, limit + 1))
    if boundary <= 0:
        raise ProviderError("provider_context_budget_exceeded", "A shortlisted candidate cannot be safely compacted within the transcript-evidence limit.")
    compacted = transcript[:boundary].rstrip()
    if not compacted:
        raise ProviderError("provider_context_budget_exceeded", "A shortlisted candidate has no safe bounded transcript evidence.")
    return compacted


class GeminiClipAnalysisProvider:
    provider_name = "gemini"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def model_name(self) -> str | None:
        return self._settings.gemini_clip_analysis_model

    def is_configured(self) -> bool:
        return bool(self._settings.gemini_api_key and self.model_name and find_spec("google.genai") is not None)

    def estimate_cost(self, candidate_count: int, transcript_seconds: float) -> float | None:
        return None

    async def _generate_content(self, prompt: str) -> object:
        """The sole Phase 4 production transport; tests replace this network boundary."""
        from google import genai

        client: Any = genai.Client(
            api_key=str(self._settings.gemini_api_key),
            http_options={"timeout": int(self._settings.gemini_clip_analysis_request_timeout_seconds * 1000)},
        )
        return await client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=generate_content_config(self._settings, self.model_name),
        )

    def analyze_candidates(self, candidates: list[CandidateWindow], language: str | None, platform: str) -> list[ProviderCandidate]:
        if not self.is_configured():
            raise ProviderError("provider_not_configured", "Gemini clip analysis is not configured.")
        payload, budget = compact_provider_payload(candidates, self._settings)
        prompt = (
            "Analyze exactly the submitted shortlist. Preserve candidate IDs and return concise, evidence-based semantic analysis. "
            "Assess hook, retention, usefulness, emotional impact, and platform suitability. Estimated Viral Potential is an estimate, never a guarantee. "
            "Do not invent candidates, alter local timing, or discuss selected/reserve/rejected decisions; final selection and duplicate filtering happen locally. "
            f"Language evidence: {language or 'automatic'}. Target platform: {platform}. Compact budget: {budget}. Candidates: {json.dumps(payload, ensure_ascii=False)}"
        )
        try:
            response = asyncio.run(self._generate_content(prompt))
            completion_error = generate_content_response_error(response)
            if completion_error is not None:
                raise completion_error
            logger.info(
                "event=gemini_clip_response_received diagnostic=%s",
                provider_structural_diagnostics(
                    response, settings=self._settings, shortlist_count=len(candidates),
                    transcript_characters=sum(len(candidate.transcript_text) for candidate in candidates),
                ),
            )
            try:
                return parse_generate_content_response(response, candidates, self._settings, platform)
            except (ValueError, TypeError, ValidationError) as error:
                logger.warning(
                    "event=gemini_clip_response_invalid diagnostic=%s",
                    provider_structural_diagnostics(
                        response, error, settings=self._settings, shortlist_count=len(candidates),
                        transcript_characters=sum(len(candidate.transcript_text) for candidate in candidates),
                    ),
                )
                raise ProviderError("provider_response_invalid", "Gemini returned an invalid clip analysis result.") from error
        except ProviderError:
            raise
        except Exception as error:
            status = getattr(error, "status_code", None)
            logger.warning(
                "event=gemini_clip_analysis_failed diagnostic=%s",
                provider_structural_diagnostics(
                    None, error, settings=self._settings, shortlist_count=len(candidates),
                    transcript_characters=sum(len(candidate.transcript_text) for candidate in candidates),
                ),
            )
            if status in {401, 403}:
                raise ProviderError("provider_authentication_failed", "Gemini rejected authentication.") from error
            if status == 429:
                raise ProviderError("provider_rate_limited", "Gemini is rate limited.", temporary=True) from error
            if status in {408, 504}:
                raise ProviderError("provider_timeout", "Gemini did not respond in time.", temporary=True) from error
            if status == 400:
                raise ProviderError("provider_invalid_model", "Gemini rejected the configured clip-analysis model or request.") from error
            if isinstance(error, (TimeoutError, OSError, ConnectionError)):
                raise ProviderError("provider_network_failed", "Gemini clip analysis could not reach the provider.", temporary=True) from error
            raise ProviderError("clip_analysis_failed", "Gemini clip analysis failed.") from error


class LocalSelectionEngine:
    """Deterministic evidence-only candidate generation and selection."""

    def generate_windows(self, segments: list[SegmentEvidence], requested_count: int, duration_mode: str) -> tuple[list[CandidateWindow], list[tuple[CandidateWindow, str]]]:
        minimum, maximum = duration_limits(duration_mode)
        candidates: list[CandidateWindow] = []
        rejected: list[tuple[CandidateWindow, str]] = []
        for start_index, start in enumerate(segments):
            words: list[str] = []
            for end_index in range(start_index, len(segments)):
                end = segments[end_index]
                words.append(end.text.strip())
                window = CandidateWindow(f"local-{start_index}-{end_index}", start.start_seconds, end.end_seconds, " ".join(words).strip(), start_index, end_index, ["segment timing only"])
                if window.duration_seconds > maximum:
                    break
                if window.duration_seconds >= minimum:
                    reason = self._invalid_reason(window, segments)
                    (rejected if reason else candidates).append((window, reason) if reason else window)  # type: ignore[arg-type]
        candidates = self._unique_windows(candidates)
        return candidates, rejected

    def _unique_windows(self, windows: list[CandidateWindow]) -> list[CandidateWindow]:
        unique: dict[str, CandidateWindow] = {}
        for item in windows:
            key = normalize_comparison_text(item.transcript_text)
            if key and key not in unique:
                unique[key] = item
        return list(unique.values())

    def shortlist(self, windows: list[CandidateWindow], requested_count: int, max_candidates: int) -> tuple[list[CandidateWindow], dict[str, str]]:
        """Choose diverse, locally valid candidates before any paid semantic analysis."""
        minimum = max(requested_count * 4, 12)
        if minimum > max_candidates:
            raise ProviderError("provider_shortlist_limit_too_low", "The configured provider shortlist limit cannot satisfy the requested clip count.")
        scored = sorted(
            windows,
            key=lambda item: (min(len(item.transcript_text.split()), 80), min(item.duration_seconds, 60.0), -item.start_seconds),
            reverse=True,
        )
        shortlist: list[CandidateWindow] = []
        reasons: dict[str, str] = {}
        for item in scored:
            duplicate = self.duplicate_reason(item, shortlist)
            if duplicate:
                reasons[item.id] = f"non_analyzed_reserve:{duplicate[1]}"
                continue
            if len(shortlist) < minimum:
                shortlist.append(item)
                reasons[item.id] = "shortlisted:complete_standalone_diverse_local_evidence"
            else:
                reasons[item.id] = "non_analyzed_reserve:lower_local_priority"
        return shortlist, reasons

    def _invalid_reason(self, window: CandidateWindow, segments: list[SegmentEvidence]) -> str | None:
        text = normalize_comparison_text(window.transcript_text)
        tokens = text.split()
        if not tokens or len(tokens) < 5:
            return "transcript_too_short"
        if " ".join(tokens[:3]) in GREETINGS or tokens[0] in GREETINGS:
            return "greeting_opening"
        if set(tokens).issubset(FILLER):
            return "filler_only"
        if window.end_seconds <= window.start_seconds:
            return "invalid_timestamp_range"
        covered = segments[window.segment_start:window.segment_end + 1]
        if any(next_item.start_seconds - item.end_seconds > 3.0 for item, next_item in zip(covered, covered[1:])):
            return "excessive_segment_gap"
        if window.transcript_text.rstrip()[-1:] not in {".", "!", "?", "؟"} and len(tokens) < 18:
            return "incomplete_ending"
        return None

    def local_analysis(self, window: CandidateWindow, platform: str) -> ProviderCandidate:
        text = window.transcript_text.strip()
        first = text.split(maxsplit=10)[0:10]
        opening = " ".join(first)
        lower = normalize_comparison_text(opening)
        hook_type = "useful_promise"
        if "?" in opening or "؟" in opening:
            hook_type = "direct_question"
        elif any(marker in lower for marker in {"خطا", "غلط", "mistake"}):
            hook_type = "common_mistake"
        elif any(marker in lower for marker in {"لا", "never", "dont"}):
            hook_type = "warning"
        elif any(marker in lower for marker in {"كيف", "how", "شلون"}):
            hook_type = "problem_first"
        immediate = 13 if len(opening.split()) >= 4 else 6
        curiosity = 16 if hook_type in {"direct_question", "common_mistake"} else 10
        emotion = 8
        specificity = 8 if any(char.isdigit() for char in text) else 6
        relevance, scroll, pacing = 12, 12, 8
        hook = min(100, immediate + curiosity + emotion + specificity + relevance + scroll + pacing)
        continuity_penalty = 8 if window.duration_seconds < 25 else 0
        retention = max(0, min(100, round(hook * .55 + 30 - continuity_penalty)))
        standalone = 72 if len(text.split()) >= 18 else 52
        usefulness = 70 if hook_type in {"common_mistake", "useful_promise", "problem_first"} else 55
        entertainment = 48
        emotional = 45
        share, save, comment, loop, visual = 54, 58, 42, 35, 45
        weaknesses = ["segment_timestamp_precision"]
        if window.duration_seconds < 25:
            weaknesses.append("short_context_window")
        viral_score = round(hook * .20 + retention * .20 + standalone * .12 + max(usefulness, entertainment) * .12 + emotional * .10 + share * .08 + save * .05 + comment * .05 + loop * .05 + visual * .03, 2)
        return ProviderCandidate(candidate_id=window.id, start_time=window.start_seconds, end_time=window.end_seconds, duration=window.duration_seconds, timestamp_precision="segment", transcript=text, topic=opening[:96] or "Transcript moment", summary=text[:320], hook_type=hook_type, hook_text=opening, hook_score=hook, hook_reason="Estimated from transcript opening evidence.", first_1_second_score=max(0, hook - 8), first_3_seconds_score=hook, first_5_seconds_score=min(100, hook + 3), retention_score=retention, retention_reason="Predicted from opening clarity, continuity, and complete segment boundaries.", standalone_score=standalone, usefulness_score=usefulness, entertainment_score=entertainment, emotional_impact_score=emotional, share_potential_score=share, save_potential_score=save, comment_potential_score=comment, loop_potential_score=loop, visual_suitability_score=visual, viral_potential_score=viral_score, confidence_score=62, ideal_platform=platform, target_audience="Short-form viewers interested in the transcript topic", likely_viewer_reaction="Estimated useful or curious response", suggested_title=opening[:120], suggested_on_screen_hook=opening[:120], detected_weaknesses=weaknesses, selection_status="reserve", selection_reason="Local evidence prepared for provider analysis.")

    def duplicate_reason(self, candidate: CandidateWindow, accepted: list[CandidateWindow]) -> tuple[str, str] | None:
        for other in accepted:
            if timeline_iou(candidate.start_seconds, candidate.end_seconds, other.start_seconds, other.end_seconds) >= .55:
                return (f"timeline-{other.id}", "timeline_overlap")
            if token_overlap(candidate.transcript_text, other.transcript_text) >= .72:
                return (f"text-{other.id}", "normalized_text_overlap")
        return None
