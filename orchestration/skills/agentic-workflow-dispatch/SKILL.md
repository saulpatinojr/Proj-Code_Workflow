---
name: agentic-workflow-dispatch
description: Plan and run a multi-agent workflow when a request needs one or more specialist agents, explicit handoffs, dependency ordering, or a verifiable completion state.
---

Use this skill when work spans specialist roles, or when the user asks for delegation, orchestration, a parallel review, a handoff, or an all-agent workflow.

The Code Workflow controller is installed once in the user profile. Run it from inside the repository as `{{controller}} <command>`; it keeps each workflow's state in `.agentic/` at the repository root. Always pass `--client` with the client id your orchestrator names, so that only specialists your client can run are selected.

## Dispatch contract

1. Read the repository's instructions, and identify the requested outcome, the authorization boundary and the acceptance criteria.
2. Run `{{controller}} discover --client <client>` when you do not know which specialists are available. Treat its output as evidence, not as authorization.
3. Choose `one`, `selected` or `all`, and mark each node required or optional.
4. Run `{{controller}} init --client <client> --mode <mode> --objective "..."` before starting any subagent. The workflow folder is the source of truth for status.
5. Plan by dependency. Run only independent nodes in parallel, and never more at once than the workflow's `max_parallel`.
6. Start each required node with your client's own subagent mechanism, using the exact registered agent name. Give it the task, the relevant files, the acceptance criteria, the authorization limits and its handoff path.
7. Require a handoff that follows [references/handoff-contract.md](references/handoff-contract.md). A summary in the conversation is not a completed handoff.
8. Run `{{controller}} gates --workflow <workflow-id>` when the repository has deterministic checks (Terraform, Ansible, npm, pytest, or the repository's own `tooling/gates.json`), then `{{controller}} validate --workflow <workflow-id>` before you summarize. Gate results outrank any agent's opinion that a check passed. Do not claim success while a required node or gate is missing, failing, blocked or unverified.
9. Summarize only from the recorded handoffs and artifacts, and keep disagreements and uncertainty visible.

## Selection rules

- `one`: select the smallest capable registered agent.
- `selected`: use the agents the user named. Each is required unless it is also listed in `--optional-agents`; a missing required agent blocks, and a missing optional one is recorded as `skipped_optional`.
- `all`: select every registered agent whose `enabled_by_default` is true. Installed ones are required, and those your client cannot run are recorded as `skipped_optional`. Use `--require-all` only when the user explicitly requires every registered role.
- Invoke a specialist once per workflow unless the workflow creates a retry node.
- Never invoke an orchestrator as a specialist node.

## Safety

Planning, discovery, inspection and local validation are the default. Ask before external publication, pull request creation, deployment, cloud or state changes, deletion, permission changes, secrets, or production work. Never use a permission-bypass mode to make delegation succeed.

Read [references/dispatch-examples.md](references/dispatch-examples.md) for one, selected and all-agent examples.
