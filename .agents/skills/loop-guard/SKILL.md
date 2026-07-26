---
name: loop-guard
description: Manual guard procedure for a separately human-approved L2 fix attempt. It never starts work, commits, pushes, merges, or automates retries.
user_invocable: true
---

# Loop Guard

Use this procedure only after a human explicitly approves one scoped L2 fix attempt. It is not used for L1 report-only triage.

## Before an attempt

1. Confirm the human-approved scope and the applicable verification command.
2. Manually read `STATE.md` for priorities and pause status, `LOOP.md` for the permitted level, `loop-constraints.md` and `docs/safety.md` for safeguards, `loop-budget.md` for limits, and recent `loop-run-log.md` records for prior outcomes.
3. If the Pause Flag is `loop-pause-all`, stop and report the pause. If the attempt would exceed the budget or violates a constraint, stop and escalate.
4. Add a manual `started` record to `loop-ledger.json` before changing files. The record must include the item id, attempt number, scope, timestamp, and intended verification.

## After an attempt

1. Run the approved verification and capture its real result.
2. Update the same ledger entry to `passed`, `failed`, or `escalated` with the verification result and a concise note.
3. After three failed attempts for the same item, do not retry; update `STATE.md` and escalate to the human.
4. Append the review outcome to `loop-run-log.md` and present it for human review.

## Non-negotiable limits

- This procedure never invokes an executable named `loop-context` or any other fabricated command.
- It never performs unattended retries, commits, pushes, pull-request actions, merges, or destructive operations.
- `loop-ledger.json` is a manual audit record only; it does not trigger work.
