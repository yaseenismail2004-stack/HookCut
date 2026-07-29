# HookCut Project Context

## Purpose

HookCut is a single-user, Windows-first, local web application for turning authorized long-form UGC video into genuine short-form clips. It supports Arabic, Iraqi Arabic, English, and mixed speech. Source media and outputs remain on the user's machine.

## Architecture and stack

- Frontend: Next.js App Router, TypeScript, Tailwind CSS, ESLint, and Vitest with Arabic RTL and English LTR support.
- Backend: Python 3.12, FastAPI, Pydantic, SQLAlchemy 2, Alembic, pytest, and Uvicorn.
- Database: local SQLite. Schema changes use Alembic migrations; application code must not rely on implicit table creation.
- Media: FFmpeg and ffprobe run locally through argument arrays only. No `shell=True`.
- Processing: one local durable worker persists job state in SQLite. No Redis, Celery, scheduler, or unattended external automation.
- AI: Gemini is the approved primary provider and OpenAI is optional. Keys are server-only, provider use is explicit, and no automatic cross-provider fallback is allowed.

## Important directories

| Directory | Purpose |
|---|---|
| `apps/web` | Next.js frontend |
| `apps/api` | FastAPI backend, Alembic configuration, and project-local virtual environment |
| `storage/uploads` | User source media; ignored by Git |
| `storage/temp` | Temporary processing media; ignored by Git |
| `storage/audio` | Extracted audio; ignored by Git |
| `storage/transcripts` | Transcript artifacts; ignored by Git |
| `storage/clips` | Rendered clips; ignored by Git |
| `storage/subtitles` | Subtitle artifacts; ignored by Git |
| `docs` | Architecture, requirements, operating, and phase documentation |
| `.agents/skills` | Project-local agent skills |
| `scripts` | Windows development and validation scripts |

## Development commands

Run from the repository root:

```powershell
npm.cmd run dev
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run test
npm.cmd run build
npm.cmd run check:environment
npm.cmd run db:migrate
```

PowerShell may block `npm.ps1`; use `npm.cmd` without weakening system execution policy. Backend commands use the project-local environment after it has been verified.

## Verification commands

```powershell
npm.cmd --prefix apps/web run lint
npm.cmd --prefix apps/web run typecheck
npm.cmd --prefix apps/web run test
npm.cmd --prefix apps/web run build
apps/api/.venv/Scripts/python.exe -m pytest apps/api/tests
apps/api/.venv/Scripts/python.exe -m mypy apps/api/src
git diff --check
git status --short
npx.cmd @cobusgreyling/loop doctor .
```

Run applicable backend, frontend, build, migration, and integration checks before declaring application work complete. Do not state that a check passed when its runtime is unavailable.

## Security and operating constraints

- Never read, print, commit, or send API keys, `.env` values, media, transcripts, local databases, or private content.
- `.gitignore` must continue excluding environments, dependencies, logs, local databases, generated media, and secrets while retaining examples, source, documentation, tests, and `.gitkeep` files.
- Do not use automatic commits, pushes, merges, destructive cleanup, background agents, or unattended execution.
- GitHub sync is permitted only to an explicitly approved private `origin` remote on `codex-live`; never force-push or merge it into `main` automatically.
- Respect `AGENTS.md`, `STATE.md`, `LOOP.md`, `docs/safety.md`, and the relevant project-local skill before meaningful work.

## Locked MVP boundaries

- Accept authorized local MP4, MOV, MKV, and WebM sources within the stated limits; validate actual media structure with ffprobe.
- Preserve real upload, validation, processing, and result states. Never simulate progress, success, downloads, clips, transcripts, or provider results.
- Keep source media local and send only the minimum required extracted audio or structured text to an explicitly selected cloud provider.
- Do not start candidate generation, clip selection, rendering, subtitle editing, authorized YouTube import, face tracking, authentication, publishing, or later phases without separate authorization.
- Refer to `docs/mvp-spec.md` for complete locked requirements and acceptance criteria.
