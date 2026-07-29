# Current Task

## Active task

Perform one explicitly authorized live Gemini Generate Content verification for the Phase 4 ultra-flat contract.

## Goal

Use the verified ultra-flat raw JSON Schema contract and Generate Content transport for exactly one Gemini request. Canonical IDs, transcript excerpts, timestamps, duration, selection status, and final selection remain local. Do not retry externally. Do not render, cut, export, download, subtitle, import YouTube video, track faces, authenticate, or publish. Never expose secrets or private speech content.

## Expected files

- `CURRENT_TASK.md`
- `PROJECT_STATUS.md`
- `CHANGELOG.md`
- `NEXT_STEPS.md`
- `.project-events.jsonl`
- `STATE.md`
- `apps/api/alembic/versions/*`
- `apps/api/src/hookcut_api/models.py`
- `apps/api/src/hookcut_api/schemas.py`
- `apps/api/src/hookcut_api/routers/*`
- `apps/api/src/hookcut_api/services/*`
- `apps/api/tests/*`
- `apps/web/src/components/*`
- `apps/web/src/lib/*`
- `docs/CANDIDATE_GENERATION.md`
- `docs/CLIP_SCORING.md`
- `docs/DUPLICATE_FILTERING.md`
- `docs/PHASE_4_VERIFICATION.md`
- `docs/PHASE_4_COMPACT_CONTRACT.md`
- `docs/PHASE_4_ULTRA_FLAT_CONTRACT.md`
- `README.md`, `docs/ARCHITECTURE.md`, `docs/PHASES.md`
- Project tracking files and `.project-events.jsonl`

## Checklist

- [x] Read the locked requirements, project tracking context, current state, skills, rubric, and required test cases.
- [x] Verify the committed Phase 3.1 baseline: frontend lint/typecheck/tests/build, backend compile/mypy/tests, and Loop doctor.
- [x] Add database migration, durable selection models, state transitions, local pipeline, and provider contract.
- [x] Add API endpoints, cost gate, retry/cancellation, and manual selection adjustment.
- [x] Add the localized frontend setup, stage state, result lists, and baseline accessibility test.
- [x] Repair the local Gemini response normalization boundary and add sanitized structural fixtures; no provider call was made.
- [x] Replace the oversized provider contract with a compact semantic-only analysis contract and deterministic local final selection.
- [x] Migrate Phase 4 clip analysis from Interactions to Generate Content and verify the transport locally.
- [x] Diagnose the last Generate Content failure from retained privacy-safe metadata and replace the provider response with an ultra-flat raw JSON Schema contract; no provider request was made.
- [ ] Complete deterministic, integration, security, and one authorized Generate Content live-provider verification (blocked: the one authorized request returned `clip_analysis_failed`).
- [ ] Commit and push only if all required checks and the real provider test pass.

## Tests required

- Frontend lint, typecheck, tests, and production build.
- Backend migration, compile, type checking, tests, startup, worker shutdown, and local integration.
- One explicitly approved live Gemini transcript-only analysis after cost handling.
- Security, Git, and Loop doctor checks.

## Current blocker

The new human-authorized bounded ultra-flat request succeeded. It reused the existing candidate pool, passed validation, and completed the durable local selection run. No second provider request was sent.

## Task status

Completed and verified pending the authorized Git checkpoint. Do not send another provider request, begin Phase 5, merge, or force-push. A temporary ignored Alembic validation database remains because the local deletion policy rejected its removal command.
