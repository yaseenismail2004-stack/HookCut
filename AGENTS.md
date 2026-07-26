# Project Instructions

## Current project state

- This repository is an empty application workspace. Do not create application code, install dependencies, or add a framework until a separate, reviewed implementation task authorizes it.
- No application test, lint, build, or type-check commands exist yet. Do not run or invent such commands; document them here only once the selected application stack supplies them.
- Before any major project, feature, integration, migration, or architecture work, invoke `$grill-me` and resolve its Blocking decisions. Do not use it for trivial edits or narrowly scoped bug fixes.

## Loop Engineering

- Operating level: L1, assisted and report-only. A human explicitly starts each review; no scheduler, background job, or unattended execution is permitted.
- Before a manual loop review, read `LOOP.md`, `STATE.md`, `loop-constraints.md`, `loop-budget.md`, and the recent entries in `loop-run-log.md`.
- Follow `docs/safety.md`. Do not commit, push, open or update pull requests, merge, or make destructive changes without explicit human authorization.
- Any future L2 fix attempt requires a separate human decision and the project-local `loop-guard` procedure.
