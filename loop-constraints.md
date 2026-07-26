# Loop Constraints

These rules are binding for every Loop Engineering review. Update this file only through a reviewed, human-authorized change; no command or automation edits it.

## Execution mode

- L1 only: assisted, manual, and report-only.
- Do not create schedulers, background jobs, unattended agents, webhooks, or automatic remediation.
- Do not install dependencies, create application files, or select an application framework without explicit human authorization.

## Push, commit, and merge

- Do not commit, push, open or modify pull requests, or merge unless the human explicitly requests that exact action.
- Never auto-merge any branch.
- Never perform destructive Git operations.

## Protected paths and systems

- Never edit `.env`, `.env.*`, `auth/`, `payments/`, `secrets/`, `credentials/`, or infrastructure configuration without explicit human authorization.
- Never expose API keys, tokens, credentials, or personal data.
- Treat external services and MCP connectors as read-only unless the human explicitly authorizes a specific write.

## Change discipline

- Always tell the human what is about to happen before a change.
- Always run applicable, existing verification before proposing a change. This empty project has no application verification commands yet.
- Never disable tests, assertions, security controls, or checks to obtain a passing result.
- Make one scoped fix per approved change and do not refactor unrelated code.
- After three failed attempts for the same approved item, stop and escalate to the human.

## Project-local context and attempts

- There is no `loop-context` executable. Before any approved retry, manually read `STATE.md` for current priorities and pause status, `LOOP.md` for the allowed operating level, and recent `loop-run-log.md` entries for prior outcomes and budget context.
- During L1, do not create attempt records: triage is report-only.
- During a separately human-approved L2 fix attempt, follow `.agents/skills/loop-guard/SKILL.md` and record each attempt in `loop-ledger.json` before retrying. The ledger is a manual audit record, not an automation trigger.

## Budget and communication

- If the estimated daily spend reaches 80% of the cap, switch to report-only and notify the human in `STATE.md`.
- If `loop-pause-all` is active in `STATE.md`, stop immediately and report that no action was taken.
- Never close an issue or pull request without explicit human approval.
