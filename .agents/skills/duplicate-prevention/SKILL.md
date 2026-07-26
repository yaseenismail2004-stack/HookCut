---
name: duplicate-prevention
description: Detect overlapping, semantically repetitive, and topic-duplicate clip candidates. Use before final selection to enforce the MVP's strict-diversity default.
---

# Duplicate Prevention

## Purpose

Ensure selected clips do not repeat the same moment, hook, conclusion, or idea.

## When to use it

Use after candidates are scored and before selection-mode rules are applied.

## Required inputs

- Candidate timestamps, original transcript, normalized comparison text, topic, hook, conclusion, audio quality, hook score, and retention score.

## Mandatory workflow

1. Preserve original text and derive comparison-only Arabic-normalized text by removing diacritics and punctuation, normalizing Alef forms and Ya/Alef Maqsura, and collapsing whitespace.
2. Compare timeline overlap, token overlap, semantic, topic, hook, and conclusion similarity.
3. Apply strict diversity by default; support balanced diversity and similar-moments-allowed only when explicitly requested.
4. Retain the stronger hook, clearer standalone meaning, complete payoff, better audio, and stronger retention; record the rejected candidate's reason.

## Output schema

`{ "candidate_id": "string", "similarity_group": "string|null", "selection_status": "selected|reserve|rejected", "rejection_reason": "string|null", "comparisons": [] }`

## Scoring and validation rules

Use stated similarity evidence rather than a single opaque score. Validate normalized Arabic comparison does not replace the original transcript.

## Rejection rules

Reject timeline-overlapping or substantively duplicate candidates under strict diversity unless no non-duplicate alternative exists and the selection mode permits a reserve.

## Prohibited shortcuts

Do not compare only titles, discard original Arabic text, or silently keep duplicates to reach count.

## Tests required

Test repeated ideas, overlapping timestamps, Arabic-normalized variants, similar hooks with different payoffs, and requested count greater than strong diverse candidates.

## Completion criteria

Every rejection has a similarity group and a readable reason; every retained candidate remains distinct under the selected diversity mode.
