# Candidate generation

Phase 4 derives clip candidates locally from contiguous, ready transcript segments. Segment start and end values are the only timing evidence available from the verified Gemini transcript; no word timings are inferred.

The generator uses the requested duration band (`auto`, `15_to_30`, `30_to_60`, or `45_to_90`) and never exceeds 90 seconds. It rejects empty, greeting-led, filler-only, invalid-range, large-gap, and clearly incomplete candidates before any provider call. It retains local rejection reasons and does not fabricate duplicates to hit a requested count.

The provider receives candidate IDs, their exact segment timings, transcript text, target platform, and language evidence only. It does not receive source video or local paths.
