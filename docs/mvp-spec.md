# AI UGC Clipper MVP Specification

## Status

**Locked on 2026-07-26; provider decision updated on 2026-07-29 by explicit human approval.** This document defines the product MVP only; it does not authorize implementation, dependency installation, framework selection, external writes, or unattended automation.

## Product and user

The MVP serves one Windows-based UGC clipper, content creator, or social-media editor through a local web interface. The user supplies a video, configures a clipping request, reviews ranked candidates, and downloads genuine rendered media.

### Successful user flow

1. Upload a local video or paste an authorized public YouTube URL.
2. For a YouTube URL, affirm ownership or permission to process the content.
3. Validate the source and show its metadata.
4. Choose a target platform, 1-10 requested clips, duration mode, language, subtitle preset, and selection mode.
5. Extract audio, transcribe it, generate candidates, rank them, remove overlaps and duplicates, and select diverse results.
6. Preview selected clips with scores and explanations.
7. Render real vertical MP4 files and let the user download each MP4 and subtitle file.

## Inputs and validation

- Accept local MP4, MOV, MKV, and WebM files, plus authorized public YouTube video URLs.
- Reject unavailable, private, DRM-protected, login-required, unsupported, playlist, and channel-wide YouTube sources. Do not bypass platform restrictions; offer local-file upload as the fallback.
- Require usable video and audio streams, 20 seconds to 2 hours duration, up to 4 GB, up to 4K, with standard variable or constant frame rates.

## Processing and performance

Use hybrid local-first processing:

- Local: FFmpeg/ffprobe validation, audio extraction, rendering, subtitle burn-in, storage, cleanup, and practical face detection/reframing.
- Cloud AI: Gemini API transcription is primary, with OpenAI optional for transcription, transcript analysis, hook scoring, semantic similarity, and ranking.
- Send audio, transcript, or structured text rather than the full source video whenever sufficient.
- Prefer safe hardware-accelerated encoding with a CPU fallback.

Reference targets on Windows with 16 GB RAM, a modern six-core CPU, SSD storage, and stable internet:

- 10-minute 1080p source to three clips: under 6 minutes.
- 60-minute 1080p source to five clips: under 20 minutes.

These are engineering targets, not universal device guarantees.

## Outputs and selection

- Render 1080x1920, 9:16 MP4 output using H.264, AAC, yuv420p, fast-start metadata, and synchronized audio.
- Support 1-10 requested clips and Auto, 15-30 second, 30-60 second, and 45-90 second duration modes. Auto normally selects 25-60 seconds around a complete idea and payoff.
- Support Instagram Reels, TikTok, and YouTube Shorts export targets. Do not publish directly to those services.
- Provide **Highest Potential** (strong clips only), **Balanced** (quality, diversity, and count), and **Exact Count** (label weaker backups) modes. Never silently lower quality merely to meet a count.
- Each result includes hook, estimated retention, viral-potential, and confidence scores; topic, duration, selection reason, suggested title, suggested on-screen hook, and detected weaknesses. Never promise virality.

Generate at least `max(requested clip count x 4, 12)` candidates. Favor a strong opening, curiosity, contrast, useful answers, relatable problems, mistakes, surprise, transformation, authenticity, opinions, complete mini-stories, and share/save/comment potential. Penalize greetings, filler, sponsorship openings, missing context, incomplete sentences, delayed payoff, repeated ideas, silence, misleading clickbait, mid-word boundaries, and emotion without useful meaning.

Strict diversity is mandatory. Compare timeline overlap, Arabic-normalized transcript overlap, semantic, topic, hook, and conclusion similarity. Retain the stronger, clearer, more complete, cleaner-audio candidate and store the rejection reason.

## Language and subtitles

- Support Arabic, Iraqi Arabic, English, mixed Arabic-English speech, and automatic detection.
- On clean speech, target at least 90% transcription accuracy for Arabic and English and 85% for Iraqi Arabic. Flag low-confidence words for review.
- Let users edit transcript and subtitle text before final rendering.
- Provide editable transcript, SRT download, ASS generation, optional burned-in captions, RTL support, at most two visible lines, safe social-control margins, phrase or word highlighting, and configurable presets. Do not redistribute proprietary fonts.
- Subtitle timing should normally be within 500 ms of speech.

## Reframing

Support portrait and landscape sources. Track one main speaker when practical, keep the face in a configurable safe area, and smooth crop movement. If tracking confidence is low, use a centered foreground with a blurred background. Never stretch the source. Permit manual crop-position adjustment before export. Multi-speaker direction and cinematic reframing are deferred.

## Cost, privacy, ownership, and storage

- Use Gemini as the initial approved AI provider behind replaceable provider abstractions; retain OpenAI as an optional explicit provider. Never automatically switch providers or spend without the user's selection and approval. Gemini Free Tier may have data-use constraints, so require the user's informed consent before sending extracted audio.
- Keep API keys server-side, estimate and display job cost when possible, cache valid analysis, avoid repeated calls, and default to a configurable ceiling of US$1.50 per source-video hour. Pause for approval before exceeding it; never silently exceed the limit.
- No authentication, public SaaS deployment, or application-owned cloud media storage in this MVP. The product is single-user, local-first, Windows-first, and accessed locally.
- Source and rendered media remain on the user's machine. Delete temporary extracted audio after success; safely clean failed-job temporary files after user retry or deletion; allow manual deletion of every project and generated file.
- Disclose third-party AI processing. Do not log API keys or expose local filesystem paths.
- The user owns supplied source media and generated outputs; the application claims no ownership.

## Failure recovery

Each processing stage has an explicit state. Preserve valid completed stages, retry a failed AI or rendering stage once automatically, then show a clear error and allow manual retry from that stage. Retain valid transcripts and candidate results. Validate every output MP4 with ffprobe and reject zero-byte, corrupt, or incomplete output. Keep readable local logs without secrets.

## Deferred features

- Direct social publishing, billing, subscriptions, team workspaces, multi-user authentication, cloud media libraries, advanced timeline editing, full brand kits, collaboration, advanced multi-speaker reframing, learning from published analytics, mobile apps, and public SaaS deployment.

## Measurable acceptance criteria

1. Accept each supported local format and only eligible authorized public YouTube URLs; reject the stated unsupported source classes with an upload fallback.
2. Enforce input limits and reject media without usable audio and video before expensive processing.
3. Produce valid, playable, downloadable 1080x1920 H.264/AAC MP4 files and SRT/ASS subtitles; ffprobe validation passes and audio remains synchronized.
4. Generate at least the required candidate count, apply strict diversity, and retain a recorded reason for each duplicate rejection.
5. Return ranked results with every required score, metadata field, and explanation; never represent a virality score as a guarantee.
6. On clean evaluation samples, meet the stated transcription targets and flag low-confidence words; subtitle timing normally stays within 500 ms.
7. Meet the stated reference-machine processing targets or report measured deviation with the source characteristics and fallback used.
8. Keep estimated AI spend at or below the configured ceiling unless the user explicitly approves an overage.
9. Preserve completed stages on failure, perform only one automatic retry, permit stage-level manual retry, and reject invalid outputs.
10. Keep source and output media local, delete temporary audio after success, support user deletion, and never log secrets or local paths.
