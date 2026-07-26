---
name: retention-analysis
description: Estimate viewer retention risks and strengths in a candidate short-form clip. Use when optimizing pacing, boundaries, and candidate ranking before export.
---

# Retention Analysis

## Purpose

Estimate likely continuation and drop points until real post-publication analytics exist.

## When to use it

Use after a candidate has valid timestamps and before final selection or boundary refinement.

## Required inputs

- Candidate transcript, timing, silence/pacing data, topic boundaries, and visual/audio change notes when available.

## Mandatory workflow

1. Assess the first 1, 3, and 5 seconds, information density, pacing, silence, repetition, delayed payoff, topic shifts, open loops, and conclusion.
2. Identify strongest and weakest timestamps and recommend safe trims.
3. Label every conclusion as an estimate.

## Output schema

`{ "estimated_retention_score": 0, "first_1_second_score": 0, "first_3_seconds_score": 0, "first_5_seconds_score": 0, "strongest_timestamp": 0.0, "weakest_timestamp": 0.0, "predicted_drop_points": [], "recommended_trim_start": 0.0, "recommended_trim_end": 0.0, "pacing_notes": "string" }`

## Scoring and validation rules

Use 0-100 evidence-based estimates. Penalize early silence, unclear opening, repetition, delayed payoff, abrupt topic changes, and incomplete endings. Verify suggested trims keep word and sentence boundaries intact.

## Rejection rules

Reject candidates with no coherent payoff, unresolved context, or no reliable timestamp evidence.

## Prohibited shortcuts

Do not represent estimated retention as actual analytics or invent audience data.

## Tests required

Test silence at start, delayed payoff, repeated idea, natural-loop ending, and incomplete ending.

## Completion criteria

Return timestamp-valid estimates and trim recommendations or a documented rejection.
