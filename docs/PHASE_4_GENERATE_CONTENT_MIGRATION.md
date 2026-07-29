# Phase 4 Generate Content transport migration

## Scope

Only the server-side Gemini clip-analysis transport changed. The verified Gemini transcription provider, storage, transcript persistence, local candidate generation, duplicate filtering, local scoring, database models, and frontend workflow remain unchanged.

## Removed compatibility problem

The former clip-analysis path used Gemini Interactions and received an SDK `Interaction` wrapper that was not compatible with the compact-response parser. Phase 4 now uses the stable asynchronous Generate Content path directly and does not traverse Interaction outputs, use Interaction response formats, or use Interaction polling in production clip analysis.

## Generate Content request

`GeminiClipAnalysisProvider` calls `client.aio.models.generate_content` with `GenerateContentConfig` using `response_mime_type="application/json"`, `response_schema=CompactClipAnalysisResponse`, `temperature=0.1`, and configurable `max_output_tokens`.

The natural-language prompt gives semantic instructions only. The Pydantic schema, not a duplicated JSON schema in the prompt, defines the exact compact response shape.

## Parsing and validation

The primary path validates `response.parsed` directly. A parsed Pydantic object, mapping, or safe list representation is validated against `CompactClipAnalysisResponse`. Only when `parsed` is unavailable does the implementation validate `response.text` with `model_validate_json`.

No Interactions wrapper parsing remains in the Phase 4 path. Missing parsed/text output, malformed JSON, unknown or duplicate candidate IDs, invalid scores, invalid relative drop points, token truncation, blocked content, and provider failures fail safely without persistence or an automatic external retry.

## Safety and limits

The request remains compact: only candidate ID, transcript excerpt, relative duration, platform, and semantic instructions are supplied. Canonical source timings, transcript records, and selection decisions remain local.

`GEMINI_CLIP_ANALYSIS_REQUEST_TIMEOUT_SECONDS` defaults to 300. `GEMINI_CLIP_ANALYSIS_MAX_OUTPUT_TOKENS` defaults to 8192, which is within the local compact-response budget for up to 12 candidates. No global environment setting is changed.

## Verification status

This is a local-only transport migration. Synthetic mocked tests cover parsed and text response paths, compact response validation, safe failures, no Interactions usage, and no automatic retry. One fresh explicitly authorized live Generate Content request is required before Phase 4 can be completed.

## Live verification status

One authorized Generate Content request was made after this migration. It failed with the safe `clip_analysis_failed` code and did not persist analysis. The failure remains intentionally sanitized; no provider response content was retained. No second request was sent. A future live attempt requires local-only failure-mapping diagnosis and fresh authorization.

## Ultra-flat follow-up

The clip-analysis path now passes a hand-controlled `response_json_schema` to Generate Content rather than the Pydantic model through `response_schema`. The new response is flat and required-only; Pydantic validates it only after it is received. `response.parsed` remains the primary path and `response.text` is a validated fallback. No Interactions clip path exists.

The previous failure cannot be classified beyond `clip_analysis_failed` because the old response/exception metadata was intentionally not retained. New privacy-safe diagnostics record finish/block reasons, usage counts, parser presence/type, limits, and sanitized exception metadata for a future authorized request. No provider request occurred during this local migration.
