# HookCut

HookCut is a local-first Windows AI UGC clipper. Phase 3 adds durable local transcription jobs, FFmpeg audio extraction, a server-side Gemini-first provider abstraction with optional OpenAI, cost approval, and timestamped transcript storage. It does not select clips, render, burn subtitles, import YouTube, track faces, or authenticate users.

## Windows quick start

From the project root:

```powershell
# Frontend dependencies
npm --prefix apps/web install

# Backend virtual environment and dependencies
python -m venv apps/api/.venv
apps\api\.venv\Scripts\python.exe -m pip install --upgrade pip
apps\api\.venv\Scripts\python.exe -m pip install -e "apps/api[dev]"
npm run db:migrate
```

Copy `.env.example` files only when you need local configuration; never commit a real `.env` file. Leave `OPENAI_API_KEY` empty during Phase 1.

## Start and stop

```powershell
npm run dev

# Stop only the API and web processes started by this project
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/stop-dev.ps1
```

- Web: `http://127.0.0.1:3000`
- API health: `http://127.0.0.1:8000/api/health`
- API capabilities: `http://127.0.0.1:8000/api/system/capabilities`

## Local uploads

`POST /api/videos/upload` accepts MP4, MOV, MKV, and WebM uploads up to 4 GB. The API streams files in bounded chunks to `storage/uploads`, validates the actual container and streams with ffprobe, and accepts only media with video, usable audio, 20 seconds to 2 hours duration, and no dimension above 3840 pixels. Rejected and cancelled uploads are removed safely. `GET /api/videos`, `GET /api/videos/{id}`, and `DELETE /api/videos/{id}` return only safe metadata; the stored filename and local paths remain private.

## Transcription setup

Copy `apps/api/.env.example` to `apps/api/.env`, then set `GEMINI_API_KEY`. `GEMINI_TRANSCRIPTION_MODEL` defaults to `gemini-2.5-flash`; set `GEMINI_TRANSCRIPTION_COST_PER_MINUTE_USD` only when you have a verified rate. Gemini is the default provider and sends the extracted temporary audio to Google for the selected job. The worker requests structured timestamped output, validates it, and confirms remote file deletion after the request. OpenAI remains optional through `OPENAI_API_KEY` and `OPENAI_TRANSCRIPTION_MODEL`. Keep all keys local and never commit them.

## Checks

```powershell
npm run check:environment
npm run lint
npm run typecheck
npm run test
npm run build
npm run verify
```

See [Development](docs/DEVELOPMENT.md), [Architecture](docs/ARCHITECTURE.md), and [Phases](docs/PHASES.md).
