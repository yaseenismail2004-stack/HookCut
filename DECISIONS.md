# Decisions

## Controlled project tracking protocol

- Date: 2026-07-29
- Related phase: cross-phase project operations
- Decision: Maintain project-local context, status, task, event, changelog, decision, and next-step records through a manual, reviewable workflow.
- Why: External prompt authors do not automatically know workspace state. These records provide a truthful handoff without granting unattended automation.
- Rejected alternatives: Relying only on chat history; automatic background synchronization; automatic commits, pushes, or merges.

## Local-first single-user architecture

- Date: 2026-07-26
- Related phase: MVP foundation
- Decision: Use a Windows-first local web application with local storage and SQLite.
- Why: Source media, rendered output, and databases remain under the user's control while local FFmpeg performs media operations.
- Rejected alternatives: Public SaaS deployment, application-owned cloud media storage, multi-user authentication, and cloud-only rendering.

## Durable local processing worker

- Date: 2026-07-29
- Related phase: Phase 3 baseline
- Decision: Persist jobs in SQLite and process them through one local worker.
- Why: Jobs remain inspectable across API restarts without Redis, Celery, or unattended external infrastructure.
- Rejected alternatives: Running long work inside HTTP requests; Redis/Celery; cloud queues.

## Gemini primary, OpenAI optional

- Date: 2026-07-29
- Related phase: Phase 3 provider integration
- Decision: Gemini is the approved primary transcription provider; OpenAI remains optional and provider selection is explicit per job.
- Why: The human explicitly approved Gemini and accepted sending extracted audio to Google. The architecture remains provider-replaceable with no automatic cross-provider spending.
- Rejected alternatives: Hard-wiring one provider permanently; automatic paid fallback; exposing keys to the frontend.
- Verification status: The Gemini backend integration remains unverified until the local Python environment is repaired.
