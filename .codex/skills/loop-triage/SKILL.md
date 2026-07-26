---
name: loop-triage
description: Produce a concise, prioritized report from human-provided or explicitly authorized read-only evidence. The report is recorded in the project state file.
user_invocable: true
---

# Loop Triage Skill

This project uses triage only for L1 assisted, report-only reviews. Do not start work autonomously.

## Permitted inputs

- Recent CI or test failures supplied by the human or available through explicitly authorized read-only access.
- Open issues or tickets supplied by the human or available through explicitly authorized read-only access.
- Recent project changes supplied by the human or available locally.
- Chat threads supplied by the human or available through explicitly authorized read-only access.
- The current project state in `STATE.md`.

## Output format

Produce a concise Markdown report with these sections:

1. **High-Priority Items** - description, impact, suggested human next step, rough effort.
2. **Watch Items** - lower-urgency items to monitor.
3. **Noise / Ignore** - items considered but not actionable.
4. **State Updates** - facts to record in `STATE.md`.

## Rules

- Prefer Watch or Noise when evidence is uncertain.
- Do not propose architectural overhauls.
- Do not contact external systems, create tickets, implement fixes, or make changes.
- Respect `loop-constraints.md`, `docs/safety.md`, and the L1 operating limits in `LOOP.md`.
