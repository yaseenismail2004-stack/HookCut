# Phase 4 verification

## Implemented local checks

- Clip-selection records and candidates are persisted through an Alembic migration.
- Candidate timing is segment-based; `timestamp_precision` is stored as `segment`.
- The worker produces local candidates, applies local pre-filters, pauses before an external provider call unless cost approval is explicit, and keeps durable state.
- Gemini structured output is strict: candidate IDs, segment timings, duration, transcript text, score ranges, and allowed platform are validated. A malformed result gets one corrective retry and is never stored as valid.
- Selected, reserve, and rejected results are available through the API and the browser UI. The UI has no render, export, subtitle, or download control.

## Remaining live verification

One explicitly approved bounded request was made using an existing authorized transcript. It created local candidates and reached Gemini after the cost gate, but no result arrived before the configured 120-second timeout. The job was safely recorded as `provider_timeout`; no result was accepted or stored. Any new live request requires separate approval. Until a response passes schema validation, live Gemini clip analysis is not verified and Phase 4 is not complete.

A later single authorized retry reused the persisted candidates with a configurable 300-second analysis timeout and a one-request cap. It returned after 117 seconds, but the response failed strict schema validation (`provider_response_invalid`). It was rejected without persistence or a second provider call. The next attempt must be preceded by offline response-shape diagnostics and new explicit human approval.

After the local schema repair, one newly authorized verification request again reused the same persisted 35 candidates with the configurable 300-second timeout. It returned a response, but strict validation again produced the safe `provider_response_invalid` outcome. No candidates were selected, reserved, rejected, or persisted from that response, and no second request was sent. Raw provider content and structural error paths were not retained to protect private transcript content; a future attempt needs a new privacy-preserving diagnostic design and explicit authorization.

## Compact-contract local verification

The provider contract was redesigned locally after the second rejected response. The provider now receives only a deterministic compact shortlist (default maximum 12) and returns semantic analysis keyed by candidate ID. It no longer echoes transcript text, timing, duration, precision, source metadata, or selection decisions. Local code joins authoritative evidence, validates all scores and relative drop points, performs duplicate filtering and final selection, and preserves non-analyzed valid candidates as reserves.

No provider request was sent for this redesign. Backend compile, mypy, all 45 tests, pip check, and an Alembic upgrade from an empty validation database passed. Frontend lint, typecheck, all 14 tests, and production build passed. A new explicitly approved bounded live verification is required before Phase 4 is complete.

## Compact live verification result

One explicitly authorized compact Gemini request was sent with the configurable 300-second timeout and a one-request external limit. The existing 35 candidates were reused. Local strict diversity produced four genuinely distinct candidates, so the request did not pad the shortlist with overlapping candidates.

Gemini returned a response, but local parsing rejected it as `provider_response_invalid`. Privacy-safe diagnostics identified an unhandled SDK `Interaction` wrapper and a response character count of 5,972. No raw response values, transcript content, provider-generated semantic text, media, paths, or credentials were retained. No analysis was persisted, no final selection was calculated, and temporary reserve statuses created for the local shortlist were restored to their pre-request candidate state. No second request was sent.

Phase 4 remains incomplete. Any next attempt requires a local-only SDK-wrapper compatibility repair and fresh explicit authorization for one request.

## Generate Content transport migration

The Phase 4 provider transport was migrated locally from Gemini Interactions to `client.aio.models.generate_content`. The compact Pydantic response model is supplied as the structured-output schema. The parser prefers `response.parsed`, uses validated JSON `response.text` only when needed, and does not retain or traverse Interactions wrappers.

Synthetic network-boundary tests cover parsed and text response paths, safe invalid output, token truncation, blocked content, HTTP error mapping, no automatic retry, and privacy-safe diagnostics. The complete backend suite (48 tests), frontend suite (14 tests), linting, type checks, production build, Alembic validation, and import checks passed. No provider request occurred during this migration. A future live Generate Content verification requires fresh explicit authorization.

## Generate Content live verification result

One explicitly authorized Generate Content request was sent after local compact preflight with the configurable 300-second timeout and one external request limit. The existing 35 candidates were reused; strict local diversity formed a four-candidate compact shortlist without padding it with duplicates.

The request failed safely with the sanitized `clip_analysis_failed` result. No response content, provider semantic values, transcript excerpts, credentials, media, paths, or raw diagnostic values were retained. No analysis or final selection was persisted, temporary local reserve statuses were restored to their original candidate state, and no second request was sent.

Phase 4 remains incomplete. A future attempt requires local-only sanitized failure-mapping diagnosis and fresh explicit authorization.

## Ultra-flat contract redesign

No provider request occurred during this redesign. The final historical failure remains classified only as `clip_analysis_failed`: the prior implementation retained no response object, exception class, status, finish reason, token metadata, or parse metadata, so a more specific provider root cause cannot be claimed.

The new contract uses raw `response_json_schema`, one flat required analysis per candidate, a maximum of 12 candidates and 600 transcript characters per candidate. It removes nested hook/retention objects, source timing, transcript echoes, drop points, provider viral totals, free-form weakness text, and provider-driven selection decisions. The provider cannot choose selected/reserve/rejected status. All final scores and selections remain local.

Offline verification after the redesign passed: backend compile, mypy, pip check, Alembic upgrade from an empty database, and 49 tests; frontend lint, TypeScript check, 14 tests, and production build. No Phase 5 behavior was added. A new live call is not yet technically justified until a human accepts that the historical failure cannot be made more specific and explicitly authorizes one bounded request.

## Ultra-flat live verification result

One newly authorized bounded Generate Content request was sent. It reused the existing 35-candidate pool and selected four valid non-duplicate candidates without regenerating the transcript, video, audio, or full candidate pool. The provider input was 2,594 characters after safe word-boundary evidence compaction. The 1,782-character raw schema has structural depth four, no references, unions, null types, defaults, or additional-properties constraints; its 1,650-token conservative output estimate is below the configured 8,192-token limit.

The response passed the ultra-flat Pydantic validation and local canonical-data join. Local final selection preserved the configured quality threshold: zero candidates met the threshold, so the completed run contains zero selected, 35 reserve, and zero rejected candidates rather than falsely marking weak output as selected. The real API returned the completed run and candidates before and after an API restart. Manual reserve promotion and restoration both returned HTTP 200, and the automatic score tuple was unchanged.

The earlier success-path implementation did not retain finish reason, usage metadata, or whether `response.parsed` versus `response.text` was used. They therefore cannot be reported for this completed request without guessing. The provider now records only privacy-safe success metadata for future requests. No source transcript, provider semantic text, media, credentials, raw response, or local path was stored in this document.

Backend compile, mypy, pip check, Alembic upgrade, worker start/stop, health smoke test, and 52 tests passed. Frontend lint, TypeScript check, 15 tests (including completed-run restoration), and the production build passed. No Phase 5 behavior was added.
