# Loop Configuration - Assisted Daily Triage (Codex)

## Operating mode

This project is configured for **L1 assisted, report-only triage**. There is no scheduler, automation, connector, background job, automatic commit, automatic merge, or destructive action configured. A human must explicitly request each review.

## Active loop

| Pattern | Invocation | Status | Allowed outcome |
|---|---|---|---|
| Daily Triage | Manual, on human request | L1 report-only | Findings recorded in `STATE.md`; no implementation action |

## Manual review workflow

1. Read `STATE.md`, `loop-constraints.md`, `loop-budget.md`, `loop-run-log.md`, and `docs/safety.md`.
2. Use the `loop-triage` skill only to summarize evidence provided in the current task or available through explicitly authorized read-only access.
3. Update `STATE.md` with concise findings and append a report-only entry to `loop-run-log.md`.
4. Present findings for human review. Stop; do not create fixes, branches, commits, pull requests, pushes, or merges.

## Human gates

- L2 or higher is not enabled. A human must explicitly authorize any future change-making loop.
- High-risk paths and all external write actions require the human review defined in `docs/safety.md`.
- A verifier is advisory only and cannot authorize a change, commit, push, or merge.

## MCP and external access

MCP connectors are not required or configured for this pattern. If a future review needs external data, a human must explicitly authorize the specific read-only access; external writes remain prohibited unless separately authorized.

## Project-local support

- Operating instructions: `AGENTS.md`
- Current state: `STATE.md`
- Binding constraints: `loop-constraints.md`
- Spending limits: `loop-budget.md`
- Review history: `loop-run-log.md`
- Safety policy: `docs/safety.md`
- Locked product requirements: `docs/mvp-spec.md`
- Guard procedure for a separately approved L2 attempt: `.agents/skills/loop-guard/SKILL.md`
- Attempt ledger used only during an approved L2 attempt: `loop-ledger.json`
