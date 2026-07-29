# Phase 4 Gemini response-schema diagnosis

## Sanitized evidence

The prior live request completed but was rejected as `provider_response_invalid`. The historical implementation stored only that safe code, not the raw response or Pydantic field paths. Therefore the exact historical wrapper key and missing-field paths cannot be reconstructed without guessing. No private transcript, media, provider payload, or credential was retained for this diagnosis.

## Confirmed contract incompatibility

The provider prompt described an estimated viral-potential value, while the strict internal Pydantic candidate model treated that value as a computed property and rejected it as an unknown field. The repaired contract accepts `viral_potential_score` explicitly and verifies that it equals the required weighted component calculation within a small rounding tolerance.

The two failed live responses also exposed a design risk: Gemini was asked to repeat authoritative local evidence and final-selection decisions for every generated candidate. That created a large, redundant contract with many unnecessary failure points. The compact redesign removes these repeated fields and limits paid analysis to a deterministic shortlist.

## Normalization boundary

The previous Interactions wrapper was the remaining transport incompatibility. The local Phase 4 transport now uses Generate Content with the compact Pydantic model as the SDK response schema. Its primary parser consumes `response.parsed`; its only fallback validates `response.text` as compact JSON when parsed output is unavailable. No Interactions output traversal or wrapper aliases remain in the Phase 4 path.

It never invents semantic data. Missing topics, scores, IDs, timestamps, reasons, selection status, or other required fields remain validation failures. Candidate IDs and exact segment timing are revalidated against the submitted candidates before persistence.

## Diagnostics and remaining verification

For a future explicitly approved live call, diagnostics record only parsing source, field names, JSON types, array lengths, response character count, a one-way response hash, and Pydantic error paths. They never write response values, transcript text, media, paths, or credentials to logs.

Local synthetic fixtures cover Generate Content parsed Pydantic objects, parsed dictionaries, JSON text fallback, missing parsed/text output, null optional arrays, missing analyses, duplicate and unknown IDs, invalid enums, invalid score totals, invalid relative drop points, token truncation, content blocking, output-limit violations, malformed JSON, no-retry behavior, and diagnostic privacy. No provider call occurred during this migration. One newly authorized Generate Content request remains required to verify the transport live.

## Final local failure diagnosis

The latest Generate Content attempt reached the provider, but the historical implementation retained only the safe `clip_analysis_failed` code. No response object, exception class, HTTP status, finish reason, prompt-feedback block reason, token metadata, parsed-object type, or response text was retained. Therefore the underlying provider cause cannot be reconstructed honestly from the available privacy-safe evidence.

The confirmed local defect was diagnostic coverage: an unmapped SDK exception was collapsed to `clip_analysis_failed` after logging only exception type and status, and no ignored local log file exists for that call. The repaired diagnostic boundary now captures safe future metadata for both returned responses and exceptions without storing semantic content. The clip-analysis model configuration is also separate from the transcription model.

The prior generated Pydantic schema was reconstructed locally for structural analysis only: 3,958 characters, 35 properties, 33 required properties, four `$defs`, four `$ref` entries, nested hook/retention/drop-point structures, and `additionalProperties` constraints. It had no unions or null types, but was still unnecessarily complex for this provider task. The new hand-controlled ultra-flat schema is 1,782 characters, has no `$defs`, `$ref`, unions, nulls, defaults, or `additionalProperties` constraints, and is validated by Pydantic only after receipt. See `docs/PHASE_4_ULTRA_FLAT_CONTRACT.md`.
