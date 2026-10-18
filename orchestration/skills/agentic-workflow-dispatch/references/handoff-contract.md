# Handoff Contract

Each invoked subagent must create or update:

```text
.agentic/workflows/<workflow-id>/handoffs/<agent-id>.yml
```

Required fields:

```yaml
workflow_id: wf-20261008-example
agent_id: terraform-expert-engineer
agent_name: terraform-expert-engineer
status: completed # completed | partial | blocked | failed_retryable | failed_terminal
summary: One concise outcome statement.
evidence:
  - path: path/to/file
    detail: What the evidence proves.
    sha256: optional; the file's sha256 at review time
artifacts:
  - path: path/to/output
    kind: source | report | plan | test | decision
risks:
  - id: RISK-001
    severity: high
    detail: Unresolved risk.
next_action: The next safe action or "none".
authorization_used: read-only
not_verified:
  - Live deployment was not performed.
```

The handoff is invalid when:

- `agent_id` does not match the registered node;
- a required field is missing;
- an evidence or artifact path is absolute or escapes the repository;
- the status is not one of the allowed values;
- the status is `completed` but none of the cited evidence or artifact files exists.

A valid handoff gives its node the status the agent reported. Only `completed` completes a node; a required node whose agent reported `blocked`, `failed_retryable` or `failed_terminal` blocks the workflow, and `partial` leaves it partial.

Evidence is bound to the content the agent reviewed, so it cannot be silently swapped after the fact:

- when an item records `sha256`, the file must still have that hash;
- the first validation that accepts a `completed` handoff stores every cited file's hash, and any later change blocks the node until the agent writes a new handoff or the reviewed content is restored;
- before that first acceptance, a cited file modified after the handoff was written blocks the node. If its content is unchanged, record its `sha256` in the handoff. Use `not_verified` to state honestly what was not checked; the controller's `export` command carries it into Code Conductor's `AgentResult.notVerified`.

The parent orchestrator may summarize a handoff, but it must not rewrite a subagent's evidence to make an incomplete result appear complete.
