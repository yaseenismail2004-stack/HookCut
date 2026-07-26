# Windows Development Environment Validation

## Status

Validated on 2026-07-26 for the locked AI UGC Clipper MVP. No application code, framework, dependency, package manifest, or mock UI was created.

**Environment readiness: NOT READY.** The validator completed with eight critical failures.

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
| Python and pip | Critical | FAIL - neither `python` nor `py` is available |
| FFmpeg and ffprobe | Critical | FAIL - not available |
| CPU H.264 / libx264 | Critical | FAIL - cannot inspect without FFmpeg |
| AAC encoding | Critical | FAIL - cannot inspect without FFmpeg |
| Project-drive capacity | Critical | FAIL - 14.28 GB free; MVP validation requires at least 20 GB |

The Windows CIM query is available outside the sandbox. The validator falls back safely to the .NET OS API when CIM is unavailable in a restricted shell.

## FFmpeg capabilities

FFmpeg is absent, so the validator could not confirm the required subtitle, ASS, scale, crop, overlay, blur, NVENC, Intel Quick Sync, or AMD AMF capabilities. This affects subtitle burn-in, vertical reframing, rendering, post-render validation, and the required CPU fallback.

The FFmpeg smoke test was **not run**: it correctly refused to generate test media until FFmpeg, ffprobe, libx264, and AAC are available. It did not leave temporary media files behind.

## Warnings

- Windows long paths are disabled or unavailable. Keep project and temporary-media paths short; enabling long paths is optional and was not changed.
- `yt-dlp` is not installed. Authorized YouTube import is optional for environment readiness but cannot be implemented until a compliant tool is selected and available.
- No known Python or FFmpeg environment-variable conflict was detected.

## Required actions before scaffolding

1. Install Python with pip, then open a new terminal and rerun the validator:

   ```powershell
   winget install Python.Python.3.12
   ```

   This is critical because the local backend, validation tooling, and media orchestration require a real Python interpreter and pip. The project validator tries `python` first and then `py`.

2. Install a full FFmpeg build with ffprobe, libx264, AAC, subtitle/ASS filters, and standard video filters, then rerun the validator:

   ```powershell
   winget install Gyan.FFmpeg
   ```

   This is critical because the MVP must validate media, render vertical H.264/AAC MP4 files, burn subtitles, and probe real output. The validator will confirm filter support, hardware encoders, CPU fallback, and the synthetic five-second smoke test after installation.

3. Free or add at least **5.72 GB** on the project drive to reach the 20 GB minimum. This is critical for safely handling sources up to 4 GB, temporary media, and rendered clips.

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
