---
name: workflow-evidence-and-recovery
description: Validate workflow evidence, classify failures, resume safely, and produce a truthful final orchestration report.
---

Use this Skill after delegation, on retries, or whenever a workflow is incomplete or a user asks whether the agents actually ran.

Run `python tooling/workflow.py gates --workflow <workflow-id>` when the repository has deterministic checks, then `python tooling/workflow.py validate --workflow <workflow-id>` (add `--check` for a read-only report). Inspect gate evidence logs, event audit records, and handoffs. Distinguish:

- agent actually invoked and completed;
- agent invoked but returned partial or blocked;
- optional agent not installed and skipped;
- required agent unavailable and workflow blocked;
- parent-only work with no agent invocation;
- static validation passed but live external behavior remains unverified.

Retry only `failed_retryable` nodes and preserve the original handoff. If a client permission, authentication, quota, or tool failure prevents execution, report the exact blocked state. Never convert a missing handoff into a successful summary.

The final report must include workflow ID, selected nodes, actually invoked nodes, skipped nodes, blocked nodes, handoff validation result, artifacts, checks performed, not-verified items, and the next safe action.

When work should continue under Code Conductor's governed cross-provider review, run `python tooling/workflow.py export --workflow <workflow-id>`. It writes `run-manifest.json` in Code Conductor's `RunManifest` shape. Code Workflow never recommends `ready` and never writes a merge decision; readiness belongs to Code Conductor.
