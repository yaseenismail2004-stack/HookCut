---
name: clip-selection-pipeline
description: Orchestrate the validated AI UGC clip candidate-selection pipeline from transcript to ranked, diverse selections. Use when preparing a complete selection plan before any media rendering.
---

# Clip Selection Pipeline

## Purpose

Coordinate validated candidate selection; render only after selection validation succeeds.

## When to use it

Use after a timestamped transcript is available and before `video-processing` is invoked.

## Required inputs

- Valid timestamped transcript, requested count (1-10), duration mode, selection mode, platform, and evidence required by hook, retention, boundary, and duplicate skills.
- Read `references/scoring-rubric.md` and `references/test-cases.md` before accepting a pipeline result.

## Mandatory workflow

1. Validate transcript; detect topic boundaries; generate at least `max(requested_count x 4, 12)` candidates.
2. Optimize boundaries; validate standalone context; score hooks; estimate retention; calculate estimated viral potential.
3. Remove timeline, semantic, and topic duplicates; ensure strict topic diversity; maintain a reserve list.
4. Apply Highest Potential, Balanced, or Exact Count rules. Highest Potential may return fewer clips; Exact Count must label weaker backups.
5. Validate the strict master output before selection; retry malformed AI results safely once, then reject them. Render only after this step succeeds.

## Output schema

Return an array of objects conforming exactly to the master schema in `docs/CLIP_SELECTION_PIPELINE.md`; no required field may be omitted.

## Scoring and validation rules

Use the rubric weights without claiming virality or actual retention analytics. Scores require stated evidence and confidence. Enforce 0-100 numeric score bounds, valid timestamps, allowed platforms, and selection-status values.

## Rejection rules

Reject malformed or incomplete AI output, invalid boundaries, non-standalone candidates, duplicates prohibited by mode, and candidates below the configured quality threshold.

## Prohibited shortcuts

Do not render before selection validation, invent candidates, hide weak Exact Count backups, return duplicates to meet count, or treat estimates as platform guarantees.

## Tests required

Run the cases in `references/test-cases.md`; include strong Arabic, Iraqi Arabic, English, mixed-language, weak greeting, delayed payoff, context, duplicate, overlap, emotion-only, calm-useful, silence, loop, incomplete-ending, and insufficient-strong-candidate cases.

## Completion criteria

Return selected and reserve candidates that validate against the master schema, the rubric, strict diversity, and the requested mode.
