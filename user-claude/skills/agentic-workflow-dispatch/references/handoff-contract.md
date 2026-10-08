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

The handoff is invalid when `agent_id` does not match the registered node, a required field is missing, an artifact path is outside the repository, or the status claims completion without evidence or an explicit not-verified statement where appropriate.

The parent orchestrator may summarize a handoff, but it must not rewrite a subagent's evidence to make an incomplete result appear complete.
