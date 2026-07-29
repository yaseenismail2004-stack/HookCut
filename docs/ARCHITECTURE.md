# Phase 1 Architecture

HookCut is a local-first Windows workspace with two independently runnable applications:

- `apps/web`: Next.js App Router UI. The browser calls the configured FastAPI health endpoint directly.
- `apps/api`: FastAPI service. It owns server-side configuration, safe capability detection, and local storage-path enforcement.
- `storage`: project-local media roots prepared for later phases. Phase 1 creates directories only; it neither uploads nor deletes media.

## Current boundary

The only application endpoints are `GET /api/health` and `GET /api/system/capabilities`. They do not expose API keys, environment values, or absolute local paths.

The frontend only shows the project foundation and real backend connection state. It does not simulate uploads, processing, results, downloads, or clip data.

## Security posture

- API configuration is read from environment variables and never sent to the browser.
- CORS accepts only the configured local web origin, with no credentials.
- Storage resolution rejects absolute paths and traversal outside the configured storage root.
- No Phase 1 code deletes storage content.

## Deferred boundaries

AI calls, media uploads, ffprobe source analysis, jobs, transcription, selection, rendering, captions, YouTube imports, face tracking, authentication, and downloads are outside Phase 1.
