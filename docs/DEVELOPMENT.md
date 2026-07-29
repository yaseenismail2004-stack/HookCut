# Windows Development

Run all commands from the project root.

## Install dependencies

```powershell
npm --prefix apps/web install
python -m venv apps/api/.venv
apps\api\.venv\Scripts\python.exe -m pip install --upgrade pip
apps\api\.venv\Scripts\python.exe -m pip install -e "apps/api[dev]"
npm run db:migrate
```

## Run locally

```powershell
npm run dev
```

The web app is available at `http://127.0.0.1:3000`; the API is available at `http://127.0.0.1:8000`.

To stop only processes recorded by this project:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/stop-dev.ps1
```

## Verify

```powershell
npm run lint
npm run typecheck
npm run test
npm run build
npm run verify
npm run db:migrate
```

## Video intake

The browser sends the selected local file only after the user presses Upload. The API streams it in bounded chunks, performs extension/content-type checks, then validates real media structure with ffprobe. Supported containers are MP4, MOV, MKV, and WebM. The default limits are 4 GB, 20 seconds minimum, two hours maximum, 4K maximum dimension, and both video and usable audio streams. SQLite data and all media below `storage/` are local and ignored by Git.
