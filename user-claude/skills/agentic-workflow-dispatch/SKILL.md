---
name: agentic-workflow-dispatch
description: Plan and execute multi-agent workflows when a request needs one or more specialist agents, explicit handoffs, dependency ordering, or a verifiable completion state.
---

Use this Skill whenever the work spans specialist roles or the user asks for delegation, orchestration, parallel review, handoff, or an all-agent workflow.

## Dispatch contract

1. Read repository instructions and identify the requested outcome, authorization boundary, and acceptance criteria.
2. Run `python tooling/workflow.py discover` when capability availability is unknown. Treat discovery output as evidence, not authorization.
3. Select `one`, `selected`, or `all` from `tooling/agent-registry.yml`. Mark each node required or optional for this workflow.
4. Run `python tooling/workflow.py init` before spawning a subagent. The workflow directory is the source of truth for status.
5. Build a dependency-aware plan. Parallelize only independent nodes and respect the workflow's `max_parallel` value.
6. Spawn each required node with the client's native subagent mechanism using the exact registered `agent_name`. Give it the task, relevant files, acceptance criteria, authorization limits, and the required handoff path.
7. Require the subagent to write or return a handoff conforming to `references/handoff-contract.md`. A natural-language summary alone is not a completed handoff.
8. Run `python tooling/workflow.py gates --workflow <workflow-id>` when the repository has deterministic checks (Terraform, Ansible, npm, pytest, or custom `tooling/gates.json`), then `python tooling/workflow.py validate --workflow <workflow-id>` before synthesis. Deterministic gate results outrank any agent's opinion that a check passed. Do not claim success while required nodes or gates are missing, failing, blocked, or unverified.
9. Synthesize only from recorded handoffs and artifacts. Preserve disagreements and uncertainty.

## Selection rules

- `one`: select the smallest capable registered agent.
- `selected`: use the explicitly named agents. Every named agent is **required** unless it is also listed in `--optional-agents`; a missing required name blocks, a missing optional name is recorded as `skipped_optional`.
- `all`: select every registry entry whose `enabled_by_default` is true. Installed selected agents are required; uninstalled entries are recorded as `skipped_optional`. Use `--require-all` only when the user explicitly requires every registry role to be present. Do not spawn a registry entry that is not installed.
- A domain agent may be invoked once per workflow unless the workflow explicitly creates a retry node.
- Never invoke the parent orchestrator as its own specialist node.

## Safety

Planning, discovery, inspection, and local validation are the default. Ask before external publication, PR creation, deployment, cloud mutation, state mutation, deletion, permission changes, secrets, or production work. Do not use permission-bypass modes as an orchestration shortcut.

Read [references/handoff-contract.md](references/handoff-contract.md) for the required handoff shape and [references/dispatch-examples.md](references/dispatch-examples.md) for one, selected, and all-agent examples.
