---
name: grill-me
description: Critically interrogates requirements before major projects, features, integrations, migrations, or architecture decisions. Use it when requirements are unclear, costly, risky, contradictory, or likely to cause rework. Do not use it for trivial edits or narrowly scoped bug fixes.
---

# Grill Me

Run a bounded discovery review before planning or implementing a major project, feature, integration, migration, or architecture decision. Do not write application code while using this skill.

## Establish context first

1. Restate the proposed project in plain language using only the request and confirmed project facts. Label unknowns as unknown; do not turn guesses into requirements.
2. Read `AGENTS.md`, `STATE.md`, `LOOP.md`, and all relevant existing project documentation before asking questions. Also read `docs/safety.md` when security, privacy, external services, or automation may be involved.
3. Extract already-confirmed decisions and list both confirmed and unconfirmed assumptions. Do not ask for information already documented.
4. Read `references/question-bank.md` and select only the sections relevant to the proposal.

## Decide what must be resolved

Classify each decision before questioning:

- **Blocking**: required to define a safe MVP, authorize external access or spend, prevent legal/privacy risk, or choose an incompatible architecture.
- **Important**: materially affects quality, cost, scale, or delivery but can be resolved after the MVP boundary is clear.
- **Can be deferred**: worthwhile enhancement that neither changes the MVP outcome nor creates material risk now.

Challenge contradictions, unsupported promises, and unrealistic targets directly. Name the trade-off and ask for a decision rather than silently choosing one.

## Conduct a focused interview

Ask the smallest useful set of focused questions, beginning with Blocking items. For a video clipping product, cover as applicable:

- target users, exact end-to-end user flow, and the MVP outcome;
- user-uploaded video versus authorized YouTube import, expected duration/file size, clip count, and real download behavior;
- delivery targets for Instagram Reels, TikTok, and YouTube Shorts;
- Arabic, Iraqi Arabic, and English handling; transcription accuracy; subtitle quality and style;
- hook and clip-selection criteria, duplicate prevention, vertical framing, and face tracking;
- processing speed, local versus cloud processing, AI provider, API costs, storage, cleanup, privacy, retention, authentication, deployment, ownership, and usage permissions;
- failure cases, retries, recovery, and measurable acceptance criteria.

Use the question bank to adapt the interview to AI, video, social, web, desktop, SaaS, and third-party API concerns. Do not ask every question mechanically: skip answered, irrelevant, or deferrable topics. Stop once the Blocking decisions are resolved and enough Important decisions are known to define a safe MVP. Never turn this into an endless interview.

## Required output

End with these sections:

1. **Confirmed requirements**
2. **Unresolved blocking questions**
3. **Important decisions**
4. **Deferred features**
5. **Risks**
6. **Locked MVP scope**
7. **Measurable completion criteria**

If any Blocking item remains unresolved, state: **Implementation is blocked pending the listed decisions.** Do not plan implementation, select a stack, install dependencies, or write application code until the user resolves them. If no Blocking item remains, state the exact MVP scope that is safe to plan next.
