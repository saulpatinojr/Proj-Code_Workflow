---
name: workflow-hooks-and-guardrails
description: Explain, review and troubleshoot Code Workflow's optional lifecycle hooks for audit records, subagent tracking and an opt-in completion check.
---

Use this skill when the user asks about Code Workflow's hooks, wants to turn them on, or is troubleshooting them.

Hooks are optional and stay off until the user turns them on. Code Workflow writes a ready-made hook configuration for each installed client into `{{pack_home}}/hooks/`; turning hooks on means merging that configuration into the client's own user settings, never overwriting what is already there. Do not turn hooks on for the user, and do not enable hooks that call external URLs without explicit authorization.

One script serves every client: `{{pack_home}}/hooks/claude_event.py`. It reads the event as JSON on standard input, writes redacted records to `.agentic/audit/` in the repository, and never uses the network. Prompts, transcripts and tool input or output are never recorded.

Where each client reads user-level hooks:

- **Claude Code:** the `hooks` key in `~/.claude/settings.json`.
- **Codex:** `~/.codex/hooks.json`. Each hook runs only after the user trusts it with `/hooks`, and again after any change.
- **Copilot CLI and VS Code's Copilot harness:** `~/.copilot/hooks/*.json`.

`SubagentStart` only records. `Stop` fails open: it can stop a session from ending only when a workflow was created with `--enforce-stop`, the controller is present, and validation fails. Claude Code and Codex honour that block; other clients only record it.

Hooks collect evidence and add a guardrail. The orchestrator must still delegate for real and validate the handoff files.
