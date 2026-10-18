---
name: handoff-contract-and-state
description: Create, inspect, validate and resume durable workflow state and the structured handoffs specialists write.
---

Use this skill when work crosses agent boundaries, must be resumable, or needs evidence that a specialist actually finished its assignment.

Each workflow's state lives in `.agentic/workflows/<workflow-id>/` at the repository root. Treat `WORKFLOW.json` and the handoff files as authoritative, and conversation summaries as secondary. Use unique workflow IDs, stable agent IDs, explicit dependencies and idempotent artifact paths. `{{controller}} status --workflow <workflow-id>` prints the current state.

The allowed outcomes are `completed`, `partial`, `blocked`, `failed_retryable`, `failed_terminal` and `skipped_optional`. A required node without a valid handoff is never `completed`.

On resume, read the existing state, keep valid handoffs, retry only retryable nodes, and do not repeat completed work unless the user asks for a fresh run. Record conflicts instead of overwriting evidence.

Read [references/state-model.md](references/state-model.md) before changing workflow state or deciding whether a run can resume.
