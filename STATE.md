# Loop State

Last reviewed: 2026-07-29 (Gemini-primary provider integration pending backend verification)
Operating level: L1 assisted, report-only
Pause state: active only when a human sets `loop-pause-all` below

## High Priority (waiting on human)

- Resolve and confirm the OpenAI account rate limit before another live transcription attempt. Three authorized job runs were rate limited; do not repeat the same external failure.

## Watch List

- Next.js App Router and FastAPI are installed only for Phase 1. Do not add AI, video-analysis, YouTube-import, rendering, subtitle, or authentication dependencies until their authorized phases.
- Phase 1 frontend reports a real backend health result; it contains no upload, processing, result, or download controls.
- Windows long paths remain optional and disabled or unavailable; keep generated media paths short.
- `yt-dlp` remains optional and is not installed. Do not add it unless a compliant authorized-import workflow is separately approved.

## Recent Review Notes

- Loop Engineering support files were repaired on 2026-07-26.
- Project-local `grill-me` requirements-discovery skill and specialized question bank were created; major project or architecture work must use it before implementation.
- All blocking AI UGC Clipper MVP product decisions were resolved and recorded in `docs/mvp-spec.md`; deferred features are explicitly excluded from the MVP.
- The project-local AI clip-selection skill suite, master schema, rubric, and text-based test cases are prepared. No application implementation, media fixtures, dependencies, or environment validation has started.
- Windows environment validation passed on 2026-07-29. Node/npm, Python 3.12.10 with pip 25.0.1, Git identity, FFmpeg/ffprobe 8.1.2, H.264/AAC, required FFmpeg filters, hardware-encoder detection, project write cleanup, OpenAI-key presence, cloud connectivity, and 65.81 GB of project-drive free space passed. The real synthetic FFmpeg smoke test produced and verified a 1080x1920 H.264/AAC MP4, then cleaned its project-local temporary media.
- Phase 1 foundation was implemented and verified: Next.js App Router frontend, FastAPI backend, real health/capabilities endpoints, storage-root enforcement, project-local development scripts, tests, lint, type checking, production build, and temporary integration smoke tests all passed. No AI, media processing, importing, rendering, subtitles, or authentication was implemented. No unattended automation was enabled.
- Phase 2 was verified: SQLite `VideoAsset` records and an Alembic migration; streamed MP4/MOV/MKV/WebM intake; ffprobe stream/container/duration/resolution validation; and safe repeatable deletion. A synthetic 21-second H.264/AAC video was uploaded through the live API, its metadata retrieved, and its physical upload removed through the live delete endpoint. No Phase 3 work was started.
- Phase 2 upload-stall fix verified: upload-body completion now enters an indeterminate validation state before the XHR response arrives; response, error, timeout, abort, and malformed-response paths all settle the UI. The browser timeout defaults to 180000 ms and is configurable via `NEXT_PUBLIC_UPLOAD_REQUEST_TIMEOUT_MS`. Structured local development logs record upload, ffprobe, database, and response milestones without paths or secrets. No Phase 3 work was started.
- Phase 3 was implemented locally: durable SQLite processing jobs, real FFmpeg FLAC audio extraction with ffprobe validation, safe artifact cleanup, a single local worker, cost-approval gates, retry/cancellation endpoints, normalized transcript persistence, and a server-only OpenAI provider abstraction. Local integration uses a test-only injected provider; no live OpenAI call has been made without a configured API key and model. No Phase 4 work was started.
- The human approved Gemini as the primary transcription provider with optional OpenAI, and approved sending extracted audio to Google. The implementation adds server-only Gemini configuration, explicit per-job provider selection, structured timestamp validation, and confirmed remote-file deletion before transcript persistence. The frontend lint, TypeScript check, 13 tests, and production build pass. Backend compile, mypy, and 18 tests pass, including offline tests for provider cleanup and cleanup-failure protection. `GEMINI_API_KEY` is not configured locally, so no Gemini request, media transfer, or live verification has occurred. Phase 4 remains unstarted.
- A controlled project tracking protocol was added: `PROJECT_CONTEXT.md`, `PROJECT_STATUS.md`, `CURRENT_TASK.md`, `CHANGELOG.md`, `NEXT_STEPS.md`, `DECISIONS.md`, and `.project-events.jsonl`. Its JSON, secret/path safety checks, ignore-rule checks, frontend lint, frontend type check, 13 frontend tests, production build, and Loop doctor passed. Backend verification remains unavailable because the local Python interpreter is missing; no tracking-system success commit was created.
- The user-created private GitHub repository is configured locally as `origin`. No branch was created and no content was pushed; the `codex-live` workflow still requires a verified checkpoint and explicit human approval.
- The human authorized publishing the verified checkpoint to `codex-live`, but the authenticated remote check timed out while awaiting interactive GitHub sign-in. Git Credential Manager is configured; no branch or content was created remotely.
- GitHub authentication was completed interactively. The verified Phase 3 checkpoint was published to `origin/codex-live`; no unverified Gemini changes, merge, or force-push were included.
- Phase 3.1 used one human-authorized ready Arabic or Iraqi Arabic source. Local FFmpeg extraction produced validated 46.5-second mono 16 kHz FLAC. The initial provider job, one separately authorized retry, and one later authorized new job each returned the sanitized `provider_rate_limited` result. The retry revalidated and reused the same ready audio artifact, with no duplicate audio created. No transcript was persisted and no source speech content is recorded in project documentation. Do not create another request until the account limit is demonstrably resolved.
- One separately authorized Gemini request used the same previously authorized source. Local extraction, the explicit cost-approval gate, and the Gemini provider stage were reached, then the job failed with the sanitized `transcription_failed` code and no transcript persisted. The implementation now records only a safe Gemini exception type and numeric status code, and reuses a validated audio artifact after cost approval. A new external request needs fresh human approval.
- A separately authorized Gemini diagnostic retry was then interrupted by a local verification-script identifier defect before any provider result was recorded. The durable job was recovered safely as `worker_interrupted`; its retry allowance is exhausted. No transcript was persisted, and another provider request requires fresh explicit human approval for a new job.
- Safe Gemini diagnostics from the first completed provider attempt report `ClientError` with HTTP status 404. A read-only model list confirms the configured `gemini-2.5-flash` is available to this key. The next approved request will log only the operation stage, exception type, and status code to distinguish upload from generation failure.
- The Gemini provider was then updated locally from the legacy generation path to the current Interactions API, with `gemini-3.6-flash` as the default model. Backend compile, mypy, 19 tests, and PowerShell verification-script syntax pass. No audio was sent during this correction; one new user-approved live request is still required.
- The first Interactions request returned a safe 400 at `interaction_generate`. The incompatible `response_mime_type` option was removed; backend compile, mypy, 19 tests, and PowerShell script syntax pass again. No transcript was persisted, and one new explicitly approved request is required to verify this exact correction.
- A subsequent explicitly approved Interactions request still returned a safe 400 after confirming the local model configuration as `gemini-3.6-flash`. Official Gemini documentation identified the missing `response_format` wrapper (`type: text`, JSON mime type, and schema). That correction is now locally covered by the backend suite; compile, mypy, and 19 tests pass. No transcript was persisted, no automatic retry occurred, and another request requires fresh explicit approval.
- Local SDK inspection then found `google-genai` 1.75.0, below the official Interactions minimum of 2.3. The API dependency now requires `google-genai>=2.3,<3`, the project-local environment runs 2.14.0, `pip check` passes, and compile/mypy/19 backend tests still pass. No audio was sent during this dependency correction; another request requires fresh explicit approval.

## Pause Flag

- Status: not paused
- To pause all manual loop activity, a human changes the status to `loop-pause-all`.

---

Run log: `loop-run-log.md`
