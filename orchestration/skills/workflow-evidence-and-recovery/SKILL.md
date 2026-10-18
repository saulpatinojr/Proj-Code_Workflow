---
name: workflow-evidence-and-recovery
description: Validate workflow evidence, classify failures, resume safely, and produce a truthful final orchestration report.
---

Use this skill after delegation, on retries, or whenever a workflow is incomplete or the user asks whether the agents actually ran.

Run `{{controller}} gates --workflow <workflow-id>` when the repository has deterministic checks, then `{{controller}} validate --workflow <workflow-id>`; add `--check` for a read-only report. Inspect the gate evidence logs, the audit records and the handoffs. Distinguish:

- an agent that was invoked and completed;
- an agent that was invoked but returned partial or blocked;
- an optional agent that is not installed and was skipped;
- a required agent that is unavailable, which blocks the workflow;
- work the orchestrator did itself without invoking any agent;
- static validation that passed while live behaviour remains unverified;
- evidence or gate results that went stale because files changed after the review or after the gates ran.

Gate results are bound to the repository's content at the time they ran. After any further change, run `gates` again before `validate`; stale results block completion.

Retry only `failed_retryable` nodes, and keep the original handoff. If a client permission, sign-in, quota or tool failure prevents a node from running, report exactly that blocked state. Never turn a missing handoff into a successful summary.

The final report states the workflow ID, the selected nodes, the nodes actually invoked, the skipped and blocked nodes, the validation result, the artifacts, the checks performed, what was not verified, and the next safe action.

When the work should continue under Code Conductor's governed cross-provider review, run `{{controller}} export --workflow <workflow-id>`. It writes `run-manifest.json` in Code Conductor's `RunManifest` shape. Code Workflow never recommends `ready` and never writes a merge decision; readiness belongs to Code Conductor.
