# HookCut

HookCut is a local-first Windows foundation for an AI UGC clipper. Phase 1 provides a real Next.js-to-FastAPI connection, safe local storage initialization, capability reporting, and development tooling. It does not upload, process, analyse, render, import, or download video.

## Windows quick start

From the project root:

```powershell
# Frontend dependencies
npm --prefix apps/web install

# Backend virtual environment and dependencies
python -m venv apps/api/.venv
apps\api\.venv\Scripts\python.exe -m pip install --upgrade pip
apps\api\.venv\Scripts\python.exe -m pip install -e "apps/api[dev]"
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
