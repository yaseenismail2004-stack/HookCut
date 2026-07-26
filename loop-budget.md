# Loop Budget

> Primary loop: **Assisted Daily Triage**. All limits apply to human-requested reviews only; no scheduler exists.

## Daily limits

| Loop | Max manual reviews/day | Max estimated tokens/day | Max sub-agent spawns/review |
|---|---:|---:|---:|
| Daily Triage (L1) | 2 | 100,000 | 0 |

## Budget procedure

1. Before a review, read the last 24 hours of `loop-run-log.md` and total any recorded `tokens_estimate` values.
2. At 80% of the daily cap, remain report-only and notify the human in `STATE.md`.
3. At 100% of the daily cap, do not start another review that day; record the decision in `STATE.md`.
4. Append an outcome record to `loop-run-log.md` only after a review is completed.

## Kill switch

- The human-controlled kill switch is the `Pause Flag` in `STATE.md`.
- If its status is `loop-pause-all`, do not perform loop work.
- Only the human may clear the pause flag.

## Cost tracking

- No cost-calculation executable is configured. Record a conservative `tokens_estimate` in each manual review entry in `loop-run-log.md`.

## Alerts This Period

- None.
