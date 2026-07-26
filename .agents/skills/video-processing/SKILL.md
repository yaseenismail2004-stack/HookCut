---
name: video-processing
description: Define safe validation, reframing, rendering, and verification requirements for genuine playable short-form video outputs. Use when planning or reviewing media processing and export behavior.
---

# Video Processing

## Purpose

Safely validate, cut, reframe, subtitle, and export genuine playable video without destructive cleanup outside the configured storage root.

## When to use it

Use for media input validation, rendering plans, crop decisions, and post-render verification.

## Required inputs

- Input path within configured storage, ffprobe metadata, target boundaries, crop settings, subtitle artifact, encoder availability, and storage-root configuration.

## Mandatory workflow

1. Use FFmpeg and ffprobe through safe subprocess argument arrays; never use `shell=True`.
2. Validate usable audio/video streams and preserve synchronization.
3. Render 1080x1920, 9:16 MP4 with H.264, AAC, yuv420p, and fast-start metadata.
4. Detect safe hardware encoding and use CPU fallback.
5. For landscape input, use stable single-speaker tracking only when confident; otherwise use centered foreground with blurred background. Never stretch and allow manual crop adjustment.
6. Validate output with ffprobe; reject corrupt, incomplete, or zero-byte files. Clean only within the configured storage root.

## Output schema

`{ "output_path": "redacted", "width": 1080, "height": 1920, "codec": "h264", "audio_codec": "aac", "validated": true, "encoder": "string", "crop_mode": "tracking|blurred-background|manual", "validation_errors": [] }`

## Scoring and validation rules

Validate dimensions, codecs, pixel format, fast-start metadata, playable duration, stream synchronization, nonzero size, and output path containment.

## Rejection rules

Reject invalid input streams, unsafe paths, unsupported render settings, failed ffprobe checks, and corrupt output.

## Prohibited shortcuts

Do not use shell command strings, stretch video, skip ffprobe validation, expose local paths, or delete outside the configured storage root.

## Tests required

Test portrait and landscape inputs, hardware fallback, tracking fallback, corrupt output, zero-byte output, synchronization, and storage-root cleanup containment.

## Completion criteria

Accept only a verified playable output with the locked MVP format or return a safe, actionable failure.
