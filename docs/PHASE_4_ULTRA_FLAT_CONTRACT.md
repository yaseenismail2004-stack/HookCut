# Phase 4 ultra-flat Gemini contract

## Purpose

Phase 4 sends Gemini only the smallest semantic-analysis request that the local selection pipeline needs. Candidate timing, transcript records, original text, duration, timestamp precision, database identifiers, final selection state, duplicate grouping, and local score totals remain authoritative in HookCut.

## Provider input

The request contains at most 12 shortlisted candidates. Each item contains a candidate identifier, at most 600 Unicode characters of transcript evidence, and a relative candidate duration. It includes the target platform and concise semantic instructions. It never includes video, audio, absolute source timings, filesystem paths, database paths, credentials, or the full transcript.

## Provider output

The raw `response_json_schema` is an object containing an `analyses` array. Each analysis has required flat fields only: `candidate_id`, `topic`, `hook_type`, fifteen 0-100 component scores, `suggested_title`, `suggested_hook`, `weakness_codes`, and `analysis_note`.

Nested hook and retention objects, transcript echoes, source timing, duration, predicted drop points, summaries, audience/reaction paragraphs, provider viral totals, and all selection decisions are deliberately excluded. Weaknesses use canonical codes only, with at most four values.

## Local canonical calculation

HookCut validates the raw JSON with Pydantic after receipt, joins it by the submitted candidate identifier, and rejects unknown, duplicate, missing, or invalid candidates. It calculates the canonical Estimated Viral Potential score as:

`0.20 × hook + 0.20 × retention + 0.12 × standalone + 0.12 × max(usefulness, entertainment) + 0.10 × emotional + 0.08 × share + 0.05 × save + 0.05 × comment + 0.05 × loop + 0.03 × visual`

The result is rounded deterministically to two decimal places; the score range is 0-100. Gemini cannot override it. Duplicate filtering, diversity, selected/reserve/rejected status, similarity groups, and decision reasons are calculated locally after complete validation.

## Transport and limits

The only Phase 4 transport is `client.aio.models.generate_content` with `response_mime_type="application/json"` and the hand-controlled `response_json_schema`. Pydantic is not passed as the SDK response schema. `response.parsed` is primary; validated JSON from `response.text` is fallback only.

The conservative 12-candidate response estimate is 8,900 characters and 4,450 tokens (two characters per token). The default 8,192 output-token cap exceeds that estimate. The request fails locally before any provider call if the context or output budget is unsafe. There is no automatic external retry.

## Privacy and diagnostics

Diagnostics retain only structural metadata: parse source, presence and types, field shapes, array counts, finish/block reasons, token counts, configured limits, validation paths, exception class/status, response length, and a one-way response hash. They never retain transcript excerpts, generated semantic text, credentials, media details, paths, or raw response values.

## Verification status

This contract is locally verified only. It requires fresh human authorization for exactly one live Generate Content request. Phase 4 is not complete.
