---
name: loop-constraints
description: Read loop-constraints.md at the start of every review and enforce its binding rules before triage or any action.
user_invocable: true
---

# Loop Constraints Enforcer

Before any work begins:

1. Read `loop-constraints.md`, `docs/safety.md`, `STATE.md`, `LOOP.md`, and `loop-budget.md`.
2. Confirm the project remains at L1 assisted, report-only mode unless the human has separately authorized a scoped L2 attempt.
3. If `loop-pause-all` is active, stop immediately and report that no action was taken.
4. Apply every constraint to the work that follows.

## Enforcement

- Before editing a file, check the protected paths in `loop-constraints.md`; escalate if the path is protected.
- Before an external write, commit, push, pull-request action, merge, dependency install, or destructive operation, stop unless the human explicitly authorized it.
- L1 triage may report findings only. It may not implement or propose fixes.
- A separately human-approved L2 attempt must follow `.agents/skills/loop-guard/SKILL.md` and record its manual attempts in `loop-ledger.json`.

## Start-of-review output

Begin with: `Constraints loaded from loop-constraints.md; L1 assisted report-only mode confirmed.`

## Interaction with local loop skills

- `loop-triage` produces concise findings only.
- `loop-budget` enforces the spending limit and early exit.
- `loop-guard` applies only to a separately human-approved L2 fix attempt.

No skill can independently authorize a change, commit, push, pull-request action, merge, or automation.
