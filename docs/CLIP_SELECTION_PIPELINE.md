# AI UGC Clipper Selection Pipeline

## Status and scope

This is a locked-MVP preparation contract, not application code. It defines the required order and structured data for clip selection. Rendering starts only after the final selection validates.

## Required order

1. Validate timestamped transcript.
2. Detect topic boundaries.
3. Generate at least `max(requested_count x 4, 12)` candidates.
4. Optimize boundaries.
5. Validate standalone context.
6. Score hooks.
7. Estimate retention.
8. Calculate estimated viral potential.
9. Remove timeline duplicates.
10. Remove semantic and topic duplicates.
11. Ensure strict topic diversity.
12. Select by Highest Potential, Balanced, or Exact Count mode.
13. Maintain a reserve list.
14. Render only after selection validation.

## Mode rules

- **Highest Potential**: return fewer than requested if strong candidates are insufficient.
- **Balanced**: balance quality, diversity, and requested count.
- **Exact Count**: attempt the requested count and clearly label weaker backup clips.

## Strict master output

Each candidate must use this shape. Reject or safely retry malformed or incomplete AI output; do not fabricate missing fields.

```json
{
  "candidate_id": "string",
  "start_time": 0.0,
  "end_time": 0.0,
  "duration": 0.0,
  "transcript": "string",
  "topic": "string",
  "summary": "string",
  "hook": {
    "type": "string",
    "text": "string",
    "score": 0,
    "reason": "string"
  },
  "retention": {
    "score": 0,
    "predicted_drop_points": [],
    "reason": "string"
  },
  "standalone_score": 0,
  "share_potential_score": 0,
  "save_potential_score": 0,
  "comment_potential_score": 0,
  "loop_potential_score": 0,
  "viral_potential_score": 0,
  "confidence_score": 0,
  "ideal_platform": "instagram|tiktok|youtube",
  "suggested_title": "string",
  "suggested_on_screen_hook": "string",
  "selection_status": "selected|reserve|rejected",
  "selection_reason": "string",
  "rejection_reason": null,
  "similarity_group": null
}
```

## Validation rules

- Numeric scores are integers from 0 to 100.
- `start_time` is non-negative; `end_time` is greater than `start_time`; `duration` matches the boundaries.
- Selection values and platform values use only the stated enumerations.
- Strict diversity is the MVP default. Preserve original Arabic text while using normalized comparison text only for similarity checks.
- Hook, retention, and viral-potential values are estimates, never guarantees or private-platform analytics.
- Full media rendering and ffprobe output validation are governed by `$video-processing` after this pipeline completes.

## Explicit invocation

Use `$clip-selection-pipeline` after validated transcription and before any rendering plan. It delegates to `$clip-boundary-optimizer`, `$hook-detection`, `$retention-analysis`, `$viral-clip-selection`, and `$duplicate-prevention`; use `$subtitle-quality` and `$video-processing` only after selection is valid.
