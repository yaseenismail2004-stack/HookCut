---
name: clip-boundary-optimizer
description: Optimize exact start and end timestamps for complete, natural short-form clips. Use after candidate windows are generated and before scoring or rendering.
---

# Clip Boundary Optimizer

## Purpose

Choose precise boundaries that preserve context, words, breaths, payoff, and natural resolution.

## When to use it

Use for every candidate window with word-level or sentence-level timestamps.

## Required inputs

- Candidate window, transcript boundaries, word timestamps, silence/breath markers when available, duration mode, and context notes.

## Mandatory workflow

1. Start before the first important word with a configurable small lead-in.
2. Remove greetings and unnecessary filler without cutting words, breaths, or required context.
3. End after a complete payoff and sentence, removing trailing silence while preserving laughter or emotional resolution.
4. Produce aggressive, balanced, and context-rich variants; use balanced as default.

## Output schema

`{ "candidate_id": "string", "aggressive": {"start_time":0.0,"end_time":0.0}, "balanced": {"start_time":0.0,"end_time":0.0}, "context_rich": {"start_time":0.0,"end_time":0.0}, "default": "balanced", "boundary_notes": [] }`

## Scoring and validation rules

Prefer immediate value, complete context, whole-word timing, complete payoff, and suitable natural loops. Validate every boundary against timestamped words and sentences.

## Rejection rules

Reject a candidate when no variant can avoid an incomplete start, cut word, missing context, or incomplete ending.

## Prohibited shortcuts

Do not trim solely to hit a duration range or end accidentally in the middle of an idea.

## Tests required

Test incomplete opening, breath near start, natural loop, trailing silence, laughter/emotional resolution, and incomplete ending.

## Completion criteria

Return three timestamp-valid versions or a clear rejection reason.
