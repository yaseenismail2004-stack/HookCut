# Windows Development Environment Validation

## Status

Validated on 2026-07-29 before Phase 1 implementation for the locked AI UGC Clipper MVP. The result remains the baseline for the current foundation.

**Environment readiness: READY — SAFE TO SCAFFOLD.** All critical and important checks pass. The only remaining findings are optional warnings.

## Detected environment

| Check | Classification | Result |
|---|---|---|
| Windows | Important | PASS - Windows 11 Home, x64 |
| PowerShell | Important | PASS - 5.1.26100.8875 |
| Node.js | Critical | PASS - v24.16.0 |
| npm | Critical | PASS - 11.13.0 |
| Git | Important | PASS - 2.54.0.windows.1; repository and identity available |
| Project write and safe temporary cleanup | Critical | PASS |
| OpenAI API key | Important | PASS - present; value was not read or displayed |
| Cloud AI HTTPS connectivity | Important | PASS |
| Project path compatibility | Optional | PASS - no known problematic characters or excessive length |
| Python | Critical | PASS - 3.12.10 |
| pip | Critical | PASS - 25.0.1 for Python 3.12 |
| FFmpeg and ffprobe | Critical | PASS - 8.1.2 full build |
| CPU H.264 / libx264 | Critical | PASS |
| AAC encoding | Critical | PASS |
| Project-drive capacity | Critical | PASS - 65.81 GB free; MVP validation requires at least 20 GB |

The Windows CIM query is available outside the sandbox. The validator falls back safely to the .NET OS API when CIM is unavailable in a restricted shell.

## FFmpeg capabilities

The full FFmpeg build provides the required `subtitles`, `ass`, `scale`, `crop`, `overlay`, and blur filters. It provides `libx264` and native AAC for the required CPU fallback. NVENC, Intel Quick Sync, and AMD AMF encoders were detected; they remain optional and require runtime hardware validation when the application is implemented.

The real smoke test **passed**. It generated a synthetic five-second source with audio, probed it, rendered a 1080x1920 MP4 using H.264, AAC, `yuv420p`, and fast-start metadata, then verified non-zero output, video and audio streams, dimensions, and duration. Temporary media was removed from the project-local validation directory.

## Warnings

- Windows long paths are disabled or unavailable. Keep project and temporary-media paths short; enabling long paths is optional and was not changed.
- `yt-dlp` is not installed. Authorized YouTube import is optional for environment readiness but cannot be implemented until a compliant tool is selected and available.
- No known Python or FFmpeg environment-variable conflict was detected.

## Remaining non-blocking observations

- Windows long paths are disabled or unavailable. This is optional; keep project, media, and temporary-media paths short.
- `yt-dlp` is not installed. Authorized YouTube import is optional for environment readiness and must not be implemented until a compliant import workflow is separately approved.

## Optional follow-up

Install a compliant `yt-dlp` distribution only after confirming the permitted authorized-import workflow:

```powershell
winget install --id yt-dlp.yt-dlp -e
```

This command was not executed. It does not authorize bypassing platform restrictions; the locked MVP still rejects unavailable, private, DRM-protected, login-required, playlist, and channel-wide sources.

## Validator behavior

Run the validator from the project root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\check-environment.ps1
```

It uses fixed argument arrays, never prints secret values, creates synthetic media only inside a unique project-local temporary directory, probes the source and final output, and removes that directory in a `finally` block.
