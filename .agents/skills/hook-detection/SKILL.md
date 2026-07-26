---
name: hook-detection
description: Detect and score scroll-stopping opening moments in timestamped video transcripts. Use when generating or evaluating candidate short-form clip openings.
---

# Hook Detection

## Purpose

Identify a compelling first 1-3 seconds without claiming virality.

## When to use it

Use after transcript timestamps and sentence boundaries are available, before final clip ranking.

## Required inputs

- Timestamped transcript with confidence values, sentence and word boundaries.
- Speech energy, silence, pacing, and candidate-window metadata when available.

## Mandatory workflow

1. Evaluate meaning, exact timing, specificity, curiosity, emotional intensity, and audience relevance.
2. Classify direct question, surprising claim, warning, common mistake, bold opinion, controversy, transformation, confession, curiosity gap, unexpected result, useful promise, numbered advice, problem-first, myth-versus-reality, or before-and-after.
3. Score the opening and retain evidence for each component.

## Output schema

`{ "type": "string", "text": "string", "start_time": 0.0, "end_time": 0.0, "score": 0, "reason": "string", "penalties": [] }`

## Scoring and validation rules

Score 0-100: immediate clarity 0-15, curiosity 0-20, emotional strength 0-15, specificity 0-10, audience relevance 0-15, scroll-stopping strength 0-15, and opening pacing 0-10. Validate that timestamps align to whole words and transcript confidence is sufficient.

## Rejection rules

Reject or heavily penalize greetings, introductions, sponsorship openings, filler, unexplained pronouns, missing context, opening silence, incomplete sentences, unsupported clickbait, low-confidence transcription, and starts inside a word.

## Prohibited shortcuts

Do not equate loudness with meaning, fabricate confidence, or describe a score as a virality guarantee.

## Tests required

Test a strong Arabic, Iraqi Arabic, English, and mixed-language hook; a weak greeting; silence at the start; and an incomplete opening.

## Completion criteria

Return a scored, timestamp-valid hook or a documented rejection reason.
