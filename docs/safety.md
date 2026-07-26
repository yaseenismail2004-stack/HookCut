# Loop Safety Policy

## Default posture

This repository is in L1 assisted, report-only mode. A human must explicitly request each loop review. No unattended execution, scheduled automation, background agents, automatic commits, automatic pulls, automatic pushes, automatic pull-request actions, automatic merges, or destructive automation is allowed.

## Required human approval

Obtain explicit approval before any action that changes project files outside a requested, reviewable task; creates a branch or commit; communicates with an external service; modifies an issue or pull request; installs dependencies; changes infrastructure; accesses production data; or performs a destructive operation.

## Protected paths and data

Do not read, reveal, or modify credentials, secrets, local environment files, authentication code, payment code, or infrastructure configuration without explicit approval. Never place secrets in source control or frontend code.

## L2 gate

L2 is disabled. Before any future L2 fix attempt, a human must explicitly authorize its scope and accept the applicable test plan. Use the project-local loop guard, keep the change to one scoped fix, preserve the three-attempt limit, and present results for review. Verification cannot independently authorize a commit, push, or merge.

## Incident and pause response

If `STATE.md` contains `loop-pause-all`, stop loop activity immediately. Record only the pause observation if the human requests a review. Escalate possible security, privacy, or data-loss risks to the human without attempting remediation.
