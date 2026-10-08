---
name: claude-hooks-and-guardrails
description: Configure and use lifecycle command hooks for orchestration audit, subagent tracking, and opt-in workflow completion checks across Claude Code, Codex, and Copilot.
---

Use this Skill when installing, reviewing, or troubleshooting the hook integration.

One script serves all clients: `hooks/claude_event.py` reads the JSON event from stdin (event name from `--event` or the payload itself, camelCase accepted), writes local audit records under `.agentic/audit/`, and never performs network calls. Stop and SubagentStop always emit a JSON object on stdout because Codex validates hook output strictly.

Per client: **Claude Code** uses the merged `.claude/settings.json` entries, anchored with `"${CLAUDE_PROJECT_DIR}/hooks/claude_event.py"`. **Codex** uses `.codex/hooks.json` (from the shipped sample); hooks run only after being reviewed and trusted via `/hooks`, and project hooks only in trusted projects. **Copilot CLI / cloud agent** uses `.github/hooks/*.json` (version 1, camelCase events, bash/powershell commands, `timeoutSec`). **VS Code Copilot** can read the Claude-format settings hooks, but only when `chat.useClaudeHooks` is enabled — it is off by default — and it ignores matcher values.

`SubagentStart` is observational. `Stop` is **fail-open**: it can block session end only when a workflow was initialized with `--enforce-stop`, the validator script exists, and validation fails; the block decision is honored by Claude Code and Codex, audit-only elsewhere. A missing or mislocated tooling directory always allows the stop.

Hooks are guardrails and evidence collection; the orchestrator still must delegate for real and validate the handoff files. Before enabling hooks in an existing repository, merge rather than overwrite settings, review command paths, and do not enable external HTTP hooks without explicit authorization.
