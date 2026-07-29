# Changelog

## 2026-07-29

- Published the previously verified Phase 3 checkpoint (`79d7b8c`) to the private `codex-live` branch. No unverified Gemini work was included.
- Verified the Gemini-primary Phase 3.1 transcription path with one explicitly approved extracted-audio request: real transcript persistence, timestamped segment retrieval after API restart, and temporary-audio cleanup.

All entries describe completed, verified checkpoints only. Unverified working-tree changes are recorded in `PROJECT_STATUS.md`, not here.

## Uncommitted local work (not a verified checkpoint)

- Redesigned the Phase 4 Gemini contract to use a compact semantic-only shortlist response; it has passed local verification but still requires one explicit live provider verification before it can become a verified checkpoint.
- Migrated the uncommitted Phase 4 clip-analysis transport from Gemini Interactions to Generate Content with locally verified Pydantic structured output; it still requires one explicit live verification before it can become a verified checkpoint.
- Replaced the uncommitted Phase 4 provider contract with a locally verified ultra-flat raw JSON Schema response and local canonical scoring; the later bounded live verification succeeded.
- Verified the Phase 4 Gemini clip-analysis pipeline with one bounded ultra-flat Generate Content request, durable persistence, restart retrieval, and manual reserve adjustment. No rendering or Phase 5 work was included.

## 2026-07-29

- Recorded the validated Windows development environment.
- Added the verified Phase 1 foundation: Next.js frontend, FastAPI backend, real health and capabilities endpoints, storage safety, scripts, tests, linting, type checks, and build verification.
- Added verified Phase 2 streamed local video intake, ffprobe validation, SQLite metadata, and safe deletion.
- Fixed and verified the upload transition from body transfer to server validation.
- Added the verified Phase 3 baseline: durable transcription jobs, real local FLAC extraction, transcript persistence, cost approval, cancellation, retry, and server-side OpenAI provider abstraction.

## 2026-07-26

- Established Loop Engineering L1 assisted, reviewable operating files.
- Locked the MVP requirements and created project-local requirements and clip-selection skills.
