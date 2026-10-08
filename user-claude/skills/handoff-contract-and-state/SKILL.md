---
name: handoff-contract-and-state
description: Create, inspect, validate, and recover durable workflow state and structured specialist handoffs.
---

Use this Skill when work crosses agent boundaries, must be resumable, or needs evidence that a specialist actually completed its assignment.

Keep the workflow state under `.agentic/workflows/<workflow-id>/`. Treat `WORKFLOW.json` and the handoff files as authoritative. Keep conversational summaries secondary. Use unique workflow IDs, stable agent IDs, explicit dependencies, and idempotent artifact paths.

Allowed terminal outcomes are `completed`, `partial`, `blocked`, `failed_retryable`, `failed_terminal`, and `skipped_optional`. A required node without a valid handoff is never `completed`.

On resume, read the existing state, preserve valid handoffs, retry only retryable nodes, and do not duplicate completed work unless the user asks for a fresh run. Record conflicts instead of overwriting evidence.

Read [references/state-model.md](references/state-model.md) when changing workflow state or deciding whether a run can be resumed.
