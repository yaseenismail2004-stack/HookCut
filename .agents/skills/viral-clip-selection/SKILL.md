---
name: viral-clip-selection
description: Estimate short-form performance potential for validated clip candidates. Use when ranking candidates after hook and retention analysis without claiming access to platform algorithms.
---

# Viral Clip Selection

## Purpose

Calculate an **Estimated Viral Potential Score**, never a guarantee of reach or virality.

## When to use it

Use only for complete, standalone candidate clips with hook and retention evidence.

## Required inputs

- Candidate transcript, topic, boundaries, hook assessment, retention assessment, and visual suitability notes.

## Mandatory workflow

1. Validate the candidate is coherent and not already rejected.
2. Score meaningful content before speech volume or emotion.
3. Produce the required result fields and detected weaknesses.

## Output schema

`{ "viral_potential_score": 0, "confidence_score": 0, "ideal_platform": "instagram|tiktok|youtube", "target_audience": "string", "hook_type": "string", "likely_viewer_reaction": "string", "suggested_title": "string", "suggested_on_screen_hook": "string", "reason_selected": "string", "detected_weaknesses": [] }`

## Scoring and validation rules

Score 0-100: hook 0-20, predicted retention 0-20, standalone clarity 0-12, usefulness/entertainment 0-12, emotion 0-10, share 0-8, save 0-5, comment 0-5, loop/replay 0-5, visual suitability 0-3. Lower confidence when transcript, visual, or context evidence is weak.

## Rejection rules

Reject incomplete-context, misleading, duplicate, or weak-candidate outputs rather than inflating a score to meet requested count.

## Prohibited shortcuts

Do not claim private Instagram, TikTok, or YouTube algorithm access; do not promise virality or rank loud speech above meaningful content automatically.

## Tests required

Test useful calm content, emotional low-value content, delayed payoff, and a strong hook with weak standalone context.

## Completion criteria

Return an evidence-backed estimate or a rejection reason, with no platform-performance guarantee.
