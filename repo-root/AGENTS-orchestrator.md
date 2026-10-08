<!-- BEGIN claude-agentic-orchestrator -->
## Agentic orchestration

This repository uses a durable multi-agent workflow harness. When work spans specialist roles or the user asks for delegation, orchestration, or an all-agent review:

- State lives under `.agentic/`; the controller is `tooling/workflow.py` (use `python` on Windows, `python3` on macOS/Linux).
- Sequence: `discover` -> `init --mode one|selected|all --objective "..."` BEFORE delegating -> delegate each required node to the matching specialist agent -> each specialist writes `.agentic/workflows/<workflow-id>/handoffs/<agent-id>.yml` (status, summary, evidence, artifacts, risks, next_action, authorization_used, not_verified) -> `validate --workflow <id>` before claiming completion.
- Missing optional agents are recorded as skipped; missing required agents block. Never report success while a required handoff is missing or invalid, and never simulate delegation.
- The registry of specialist roles is `tooling/agent-registry.yml`, regenerated from the agents installed across all ecosystems (.claude/agents, .github/agents, ~/.copilot/agents, .codex/agents) by `workflow.py registry`.
<!-- END claude-agentic-orchestrator -->
