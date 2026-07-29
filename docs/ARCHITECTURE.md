# Phase 3 Architecture

HookCut is a local-first Windows workspace with two independently runnable applications:

- `apps/web`: Next.js App Router UI. The browser calls the configured FastAPI health endpoint directly.
- `apps/api`: FastAPI service. It owns server-side configuration, safe capability detection, and local storage-path enforcement.
- `storage`: project-local media roots. Phase 2 accepts files only beneath `storage/uploads`; rejected and explicitly deleted files are removed only through root-enforced paths.
- SQLite stores `VideoAsset` metadata. Alembic owns the schema migration; startup runs `upgrade head` before the API process is launched.
- SQLite also stores durable processing jobs, audio artifacts, transcripts, timestamped segments, and timestamped words. One in-process local worker claims explicitly created jobs; it is not a scheduler or unattended external automation.

## Current boundary

The application endpoints are `GET /api/health`, `GET /api/system/capabilities`, `POST /api/videos/upload`, `GET /api/videos`, `GET /api/videos/{id}`, and `DELETE /api/videos/{id}`. They do not expose API keys, stored filenames, environment values, or absolute local paths.

Phase 3 adds transcription job creation, status, approval, cancellation, retry, per-video job listing, and transcript retrieval endpoints. The worker extracts mono 16 kHz FLAC locally, validates it with ffprobe, and sends only the audio to a configured provider.

The frontend only shows the project foundation and real backend connection state. It does not simulate uploads, processing, results, downloads, or clip data.

## Security posture

- API configuration is read from environment variables and never sent to the browser.
- CORS accepts only the configured local web origin, with no credentials.
- Storage resolution rejects absolute paths and traversal outside the configured storage root.
- Uploads stream in 1 MiB chunks, enforce the configured size limit during receipt, use cryptographically random server-side filenames, and validate claimed format plus actual ffprobe structure.
- ffprobe is invoked with an argument array and timeout; no shell command is created from user input.
- Deletion is idempotent and constrained to the matching upload path below the storage root.
- Gemini is the primary server-only provider and OpenAI is optional. Provider selection is explicit per job; there is no automatic cross-provider fallback or automatic spend. Gemini receives only the temporary extracted audio, returns structured timestamped transcript data, and its remote file deletion must be confirmed before local transcript storage. Cost must be estimated and remain under the source-duration-scaled ceiling, or the job pauses for explicit approval.
- Temporary audio is removed after a stored successful transcript or failed incomplete extraction.

## Deferred boundaries

Selection, rendering, captions, YouTube imports, face tracking, authentication, and downloads remain outside Phase 3.
