---
name: subtitle-quality
description: Validate and prepare editable, synchronized multilingual subtitles for AI UGC clips. Use when producing transcript, SRT, ASS, or burned-in caption outputs.
---

# Subtitle Quality

## Purpose

Produce accurate, editable, synchronized Arabic, Iraqi Arabic, English, and mixed-language captions.

## When to use it

Use after transcription and before subtitle export or burn-in rendering.

## Required inputs

- Timestamped transcript, word confidence, language detection, subtitle preset, safe-margin configuration, and configurable system font paths.

## Mandatory workflow

1. Preserve language meaning and RTL direction; do not literally translate Iraqi Arabic when meaning is harmed.
2. Group readable phrases, correct punctuation, mark low-confidence words, and keep no more than two visible lines.
3. Produce editable transcript, SRT, ASS, and optional burned-in caption instructions with phrase or word highlighting.

## Output schema

`{ "language": "string", "transcript": [], "srt": "string", "ass": "string", "burn_in_optional": true, "low_confidence_words": [], "timing_notes": [] }`

## Scoring and validation rules

Validate timestamp order, RTL rendering, safe margins, phrase grouping, and normal timing within 500 ms of speech. Flag rather than conceal uncertain words.

## Rejection rules

Reject malformed timestamps, overlapping lines that cannot be resolved, missing required text, or unavailable configured font paths.

## Prohibited shortcuts

Do not bundle or redistribute proprietary fonts, silently alter meaning, or claim unverified transcription accuracy.

## Tests required

Test Arabic RTL, Iraqi Arabic meaning preservation, English, mixed Arabic-English, low-confidence words, two-line limit, and timing drift.

## Completion criteria

Return editable, valid subtitle artifacts or explicit validation failures.
