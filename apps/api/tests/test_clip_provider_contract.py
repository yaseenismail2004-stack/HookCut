from __future__ import annotations

import copy
import inspect
import json

import pytest
from pydantic import ValidationError

from hookcut_api.config import Settings
from hookcut_api.services.clip_selection import (
    CandidateWindow,
    GeminiClipAnalysisProvider,
    UltraFlatClipAnalysisResponse,
    calculate_viral_potential,
    compact_provider_payload,
    _compact_evidence,
    generate_content_config,
    generate_content_response_error,
    normalize_provider_response,
    parse_generate_content_response,
    provider_structural_diagnostics,
    schema_metrics,
    ultra_flat_response_json_schema,
)
from hookcut_api.services.transcription import ProviderError


SETTINGS = Settings(storage_root="storage-test", database_url="sqlite:///storage-test/contract.db", worker_enabled=False)
PROVIDER_SETTINGS = Settings(storage_root="storage-test", database_url="sqlite:///storage-test/provider.db", worker_enabled=False, gemini_api_key="test-only-key")


def candidates(count: int = 1) -> list[CandidateWindow]:
    return [CandidateWindow(f"candidate-{index}", index * 20.0, (index + 1) * 20.0, f"Neutral synthetic evidence {index}.", index, index, ["segment timing only"]) for index in range(count)]


def analysis(candidate_id: str) -> dict[str, object]:
    return {
        "candidate_id": candidate_id, "topic": "neutral topic", "hook_type": "useful_promise",
        "hook_score": 50, "first_1_second_score": 45, "first_3_seconds_score": 50,
        "first_5_seconds_score": 55, "retention_score": 50, "standalone_score": 50,
        "usefulness_score": 50, "entertainment_score": 50, "emotional_score": 50,
        "share_score": 50, "save_score": 50, "comment_score": 50, "loop_score": 50,
        "visual_score": 50, "confidence_score": 50, "suggested_title": "neutral title",
        "suggested_hook": "neutral hook", "weakness_codes": [], "analysis_note": "neutral evidence",
    }


def payload(count: int = 1) -> dict[str, object]:
    return {"analyses": [analysis(item.id) for item in candidates(count)]}


class GenerateResponse:
    def __init__(self, parsed: object | None = None, text: str | None = None, finish_reason: str | None = None, *, blocked: str | None = None) -> None:
        self.parsed = parsed
        self.text = text
        self.candidates = [type("Candidate", (), {"finish_reason": finish_reason})()] if finish_reason else []
        self.prompt_feedback = type("Feedback", (), {"block_reason": blocked})() if blocked else None
        self.usage_metadata = type("Usage", (), {"prompt_token_count": 12, "candidates_token_count": 24})()


def test_raw_json_schema_is_ultra_flat_and_free_of_risky_constructs() -> None:
    schema = ultra_flat_response_json_schema("gemini-3.6-flash")
    rendered = json.dumps(schema)
    metrics = schema_metrics(schema)
    assert schema["type"] == "object"
    assert "response_schema" not in rendered
    for forbidden in ("anyOf", "oneOf", "allOf", '"null"', "$ref", "additionalProperties", "default"):
        assert forbidden not in rendered
    assert metrics["maximum_nesting_depth"] == 4
    assert metrics["$ref_count"] == 0
    assert metrics["has_null_type"] is False


def test_gemini_two_schema_adds_property_ordering_only_when_required() -> None:
    assert "propertyOrdering" not in json.dumps(ultra_flat_response_json_schema("gemini-3.6-flash"))
    assert "propertyOrdering" in json.dumps(ultra_flat_response_json_schema("gemini-2.0-flash"))


def test_sdk_config_uses_response_json_schema_not_pydantic_response_schema() -> None:
    config = generate_content_config(SETTINGS, "gemini-3.6-flash")
    dumped = config.model_dump(by_alias=False, exclude_none=True)
    assert dumped["response_json_schema"]["type"] == "object"
    assert "response_schema" not in dumped
    assert dumped["response_mime_type"] == "application/json"


def test_clip_analysis_model_is_separate_from_the_transcription_model() -> None:
    settings = Settings(
        storage_root="storage-test", database_url="sqlite:///storage-test/models.db", worker_enabled=False,
        gemini_api_key="test-only-key", gemini_transcription_model="transcription-model",
        gemini_clip_analysis_model="clip-analysis-model",
    )
    assert GeminiClipAnalysisProvider(settings).model_name == "clip-analysis-model"


def test_parsed_dictionary_and_text_fallback_join_only_local_evidence() -> None:
    canonical = UltraFlatClipAnalysisResponse.model_validate(payload())
    for response in (GenerateResponse(parsed=canonical), GenerateResponse(parsed=payload()), GenerateResponse(text=json.dumps(payload()))):
        result = parse_generate_content_response(response, candidates(), SETTINGS)
        assert result[0].candidate_id == "candidate-0"
        assert result[0].transcript == "Neutral synthetic evidence 0."
        assert result[0].start_time == 0
        assert result[0].viral_potential_score == 50
        assert result[0].selection_status == "reserve"


@pytest.mark.parametrize("mutate", [
    lambda body: body["analyses"].pop(),
    lambda body: body["analyses"].append(analysis("candidate-0")),
    lambda body: body["analyses"].append(analysis("candidate-extra")),
    lambda body: body["analyses"].__setitem__(0, analysis("unknown")),
    lambda body: body["analyses"][0].pop("topic"),
    lambda body: body["analyses"][0].__setitem__("hook_score", 101),
    lambda body: body["analyses"][0].__setitem__("hook_type", "unknown"),
    lambda body: body["analyses"][0].__setitem__("weakness_codes", ["not_a_code"]),
    lambda body: body["analyses"][0].__setitem__("weakness_codes", ["filler"] * 5),
    lambda body: body["analyses"][0].__setitem__("topic", "x" * 61),
    lambda body: body["analyses"][0].__setitem__("analysis_note", "x" * 181),
    lambda body: body["analyses"][0].__setitem__("viral_potential_score", 50),
])
def test_rejects_invalid_flat_semantics(mutate: object) -> None:
    raw = payload()
    mutate(raw)  # type: ignore[operator]
    with pytest.raises((ValueError, ValidationError)):
        normalize_provider_response(raw, candidates(), SETTINGS)


def test_flat_twelve_candidate_response_and_local_selection_state() -> None:
    result = parse_generate_content_response(GenerateResponse(parsed=payload(12)), candidates(12), SETTINGS, "tiktok")
    assert len(result) == 12
    assert result[0].ideal_platform == "tiktok"
    assert all(item.selection_status == "reserve" for item in result)


def test_missing_malformed_truncated_and_safety_output_are_safe_failures() -> None:
    with pytest.raises(ValueError):
        parse_generate_content_response(GenerateResponse(), candidates(), SETTINGS)
    with pytest.raises(ValidationError):
        parse_generate_content_response(GenerateResponse(text="{not json"), candidates(), SETTINGS)
    assert generate_content_response_error(GenerateResponse(finish_reason="MAX_TOKENS")).code == "provider_output_truncated"
    assert generate_content_response_error(GenerateResponse(finish_reason="SAFETY")).code == "provider_content_blocked"
    assert generate_content_response_error(GenerateResponse(blocked="SAFETY")).code == "provider_content_blocked"


def test_payload_and_output_budget_are_conservative_and_bounded() -> None:
    compact, estimate = compact_provider_payload(candidates(12), SETTINGS)
    assert len(compact) == 12
    assert "relative_duration_seconds" in compact[0]
    assert "start_seconds" not in compact[0]
    assert estimate["expected_response_tokens"] < SETTINGS.gemini_clip_analysis_max_output_tokens
    with pytest.raises(Exception, match="shortlist"):
        compact_provider_payload(candidates(13), SETTINGS)


def test_transcript_evidence_is_compacted_only_at_a_safe_word_boundary() -> None:
    original = "word " * 200
    compacted = _compact_evidence(original, 100)
    assert len(compacted) <= 100
    assert compacted.split()[-1] == "word"
    with pytest.raises(ProviderError, match="cannot be safely compacted"):
        _compact_evidence("x" * 101, 100)


def test_local_viral_score_is_canonical_and_deterministic() -> None:
    assert calculate_viral_potential(*([0.0] * 11)) == 0
    assert calculate_viral_potential(*([100.0] * 11)) == 100
    assert calculate_viral_potential(*([50.0] * 11)) == 50
    raw = payload()
    raw["analyses"][0]["hook_score"] = -1  # type: ignore[index]
    with pytest.raises(ValidationError):
        normalize_provider_response(raw, candidates(), SETTINGS)


def test_safe_diagnostics_never_include_semantic_text_or_credentials() -> None:
    raw = GenerateResponse(text=json.dumps({"analyses": [{"topic": "private speech", "suggested_title": "secret title", "analysis_note": "do not retain"}]}))
    diagnostic = provider_structural_diagnostics(raw, settings=SETTINGS, shortlist_count=1, transcript_characters=42)
    rendered = json.dumps(diagnostic)
    for forbidden in ("private speech", "secret title", "do not retain", "test-only-key"):
        assert forbidden not in rendered
    assert diagnostic["response_hash"]
    assert diagnostic["finish_reasons"] == []
    assert diagnostic["prompt_token_count"] == 12


def test_phase_four_provider_uses_generate_content_and_never_interactions() -> None:
    source = inspect.getsource(GeminiClipAnalysisProvider)
    assert "aio.models.generate_content" in source
    assert "interactions" not in source


def test_provider_has_no_automatic_external_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = GeminiClipAnalysisProvider(PROVIDER_SETTINGS)
    calls = 0

    async def invalid_response(_: str) -> object:
        nonlocal calls
        calls += 1
        return GenerateResponse()

    monkeypatch.setattr(provider, "_generate_content", invalid_response)
    with pytest.raises(ProviderError, match="invalid clip analysis"):
        provider.analyze_candidates(candidates(), "en", "instagram")
    assert calls == 1


@pytest.mark.parametrize("status,code", [(401, "provider_authentication_failed"), (429, "provider_rate_limited"), (504, "provider_timeout")])
def test_generate_content_http_errors_are_safely_mapped(monkeypatch: pytest.MonkeyPatch, status: int, code: str) -> None:
    provider = GeminiClipAnalysisProvider(PROVIDER_SETTINGS)

    class FakeFailure(Exception):
        status_code = status

    async def fail(_: str) -> object:
        raise FakeFailure()

    monkeypatch.setattr(provider, "_generate_content", fail)
    with pytest.raises(ProviderError) as error:
        provider.analyze_candidates(candidates(), "en", "instagram")
    assert error.value.code == code


def test_generate_content_parsed_network_boundary_can_be_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = GeminiClipAnalysisProvider(PROVIDER_SETTINGS)

    async def response(_: str) -> object:
        return GenerateResponse(parsed=payload())

    monkeypatch.setattr(provider, "_generate_content", response)
    assert len(provider.analyze_candidates(candidates(), "en", "instagram")) == 1
