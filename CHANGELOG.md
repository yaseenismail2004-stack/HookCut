# Changelog

## 2026-07-29

- Published the previously verified Phase 3 checkpoint (`79d7b8c`) to the private `codex-live` branch. No unverified Gemini work was included.
- Verified the Gemini-primary Phase 3.1 transcription path with one explicitly approved extracted-audio request: real transcript persistence, timestamped segment retrieval after API restart, and temporary-audio cleanup.

All entries describe completed, verified checkpoints only. Unverified working-tree changes are recorded in `PROJECT_STATUS.md`, not here.

## Verified Phase 4 checkpoint

- Commit `d00a1e1` contains the Phase 4 Gemini clip-analysis pipeline: compact shortlisting, ultra-flat Generate Content transport, local scoring and final selection, durable persistence, API/frontend workflow, tests, and documentation. One bounded live request verified persistence and restart retrieval. No rendering or Phase 5 work was included.

## 2026-07-29

- Recorded the validated Windows development environment.
- Added the verified Phase 1 foundation: Next.js frontend, FastAPI backend, real health and capabilities endpoints, storage safety, scripts, tests, linting, type checks, and build verification.
- Added verified Phase 2 streamed local video intake, ffprobe validation, SQLite metadata, and safe deletion.
- Fixed and verified the upload transition from body transfer to server validation.
- Added the verified Phase 3 baseline: durable transcription jobs, real local FLAC extraction, transcript persistence, cost approval, cancellation, retry, and server-side OpenAI provider abstraction.

## 2026-07-26

- Established Loop Engineering L1 assisted, reviewable operating files.
- Locked the MVP requirements and created project-local requirements and clip-selection skills.
