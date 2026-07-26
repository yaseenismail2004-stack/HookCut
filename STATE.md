# Loop State

Last reviewed: 2026-07-26 (Windows environment validation completed)
Operating level: L1 assisted, report-only
Pause state: active only when a human sets `loop-pause-all` below

## High Priority (waiting on human)

- The AI UGC Clipper MVP requirements are locked in `docs/mvp-spec.md`. Environment validation is not ready: Python/pip, FFmpeg/ffprobe with H.264/AAC support, and at least 20 GB of project-drive free space are required before scaffolding.

## Watch List

- Select an implementation stack and verification plan only after separate authorization to begin implementation.
- Define project test, lint, build, and type-check commands after the stack is selected.
- Rerun `scripts/check-environment.ps1` after the documented prerequisite actions; see `docs/ENVIRONMENT.md`.

## Recent Review Notes

- Loop Engineering support files were repaired on 2026-07-26.
- Project-local `grill-me` requirements-discovery skill and specialized question bank were created; major project or architecture work must use it before implementation.
- All blocking AI UGC Clipper MVP product decisions were resolved and recorded in `docs/mvp-spec.md`; deferred features are explicitly excluded from the MVP.
- The project-local AI clip-selection skill suite, master schema, rubric, and text-based test cases are prepared. No application implementation, media fixtures, dependencies, or environment validation has started.
- Windows environment validation completed. Node/npm, Git, write cleanup, OpenAI-key presence, and cloud connectivity passed; Python/pip, FFmpeg/ffprobe/H.264/AAC, and disk-space checks failed. The FFmpeg smoke test was safely skipped because its prerequisites are absent.
- No triage findings, application changes, automated jobs, commits, pushes, or merges have been made.

## Pause Flag

- Status: not paused
- To pause all manual loop activity, a human changes the status to `loop-pause-all`.

---

Run log: `loop-run-log.md`
