---
name: loop-budget
description: Check budget and review-log spend before and after a manual loop review. Enforces an early exit when over budget or when no actionable work exists.
---

# Loop Budget Guard

Run at the start and end of every human-requested loop review.

## Start of review

1. Read `loop-budget.md` for daily caps and the `STATE.md` Pause Flag.
2. Read the last 24 hours of `loop-run-log.md` and total `tokens_estimate` values for the active pattern.
3. At 80% of the cap, remain report-only. At 100%, do not start a new review that day.
4. If `loop-pause-all` is active or there is no actionable work, stop and state why in `STATE.md`.

## End of review

Append one valid record using the schema in `loop-run-log.md`. Record only real review outcomes and conservative token estimates.

## Rules

- This project permits zero sub-agent spawns at L1.
- Do not create a scheduler, automation, or background task.
- On self-throttle, update `loop-budget.md` under **Alerts This Period** and notify the human in `STATE.md`.
