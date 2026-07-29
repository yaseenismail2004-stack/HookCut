# Project Instructions

## Current project state

- This repository is an empty application workspace. Do not create application code, install dependencies, or add a framework until a separate, reviewed implementation task authorizes it.
- No application test, lint, build, or type-check commands exist yet. Do not run or invent such commands; document them here only once the selected application stack supplies them.
- Before any major project, feature, integration, migration, or architecture work, invoke `$grill-me` and resolve its Blocking decisions. Do not use it for trivial edits or narrowly scoped bug fixes.
- For AI UGC clip analysis, use `$hook-detection`, `$retention-analysis`, `$viral-clip-selection`, `$duplicate-prevention`, and `$clip-boundary-optimizer` in the master `$clip-selection-pipeline` order. Use `$subtitle-quality` for subtitle artifacts and `$video-processing` for media validation and export plans.
- Follow `docs/CLIP_SELECTION_PIPELINE.md`; do not render before a selection validates against its master output schema.

## Loop Engineering

- Operating level: L1, assisted and report-only. A human explicitly starts each review; no scheduler, background job, or unattended execution is permitted.
- Before a manual loop review, read `LOOP.md`, `STATE.md`, `loop-constraints.md`, `loop-budget.md`, and the recent entries in `loop-run-log.md`.
- Follow `docs/safety.md`. Do not commit, push, open or update pull requests, merge, or make destructive changes without explicit human authorization.
- Any future L2 fix attempt requires a separate human decision and the project-local `loop-guard` procedure.

## Project Change Tracking

- Before every meaningful development task, read `PROJECT_CONTEXT.md`, `PROJECT_STATUS.md`, `CURRENT_TASK.md`, `STATE.md`, and the relevant project-local skills. Record `task_started` in `.project-events.jsonl` and update `CURRENT_TASK.md` before changing files.
- After each meaningful group of changes, run `git diff --stat`, inspect the actual diff, update `CURRENT_TASK.md`, and append a truthful `files_changed` event.
- Before declaring a task complete, run all applicable tests, lint, type checks, production build, and relevant integration checks. Then update `PROJECT_STATUS.md`, `CHANGELOG.md`, `NEXT_STEPS.md`, `STATE.md`, and the event log.
- Keep the tracking files truthful. Never represent unavailable or failed checks as successful, and never record secrets, private media, transcripts, environment values, or absolute local paths.
- Do not commit broken or unverified work. Never automatically merge `codex-live` into `main`; only push to a configured private remote after explicit human authorization.
