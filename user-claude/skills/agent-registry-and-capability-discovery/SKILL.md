---
name: agent-registry-and-capability-discovery
description: Discover installed specialist agents across ecosystems and map them to capabilities, required or optional workflow nodes, and safe invocation names.
---

Use this Skill before dispatch when the user asks for any, all, available, installed, or best agent, or when the requested role is not known.

The registry lives at `tooling/agent-registry.yml`, beside the workflow script, and is **generated from installed agents** by `python tooling/workflow.py registry`. Discovery scans every ecosystem: `.claude/agents` and `~/.claude/agents` (markdown), `.github/agents` and `~/.copilot/agents` (.agent.md), `.codex/agents` and `~/.codex/agents` (TOML). Each registry entry records which clients carry the agent. Regenerate whenever agents are installed or removed; never hand-maintain agent names that are not actually installed. Then run `python tooling/workflow.py discover`. Discovery is always fresh; there is no cache that can hide a newly installed agent.

Classify each requested node:

- `available`: matching agent exists and is enabled for this project.
- `optional-unavailable`: not installed or disabled and the workflow permits omission.
- `required-unavailable`: not installed or disabled and the workflow requires it.
- `ambiguous`: more than one agent claims the capability; stop and select explicitly.

Do not infer that a Skill is an agent. Skills provide knowledge or workflows; only an actual subagent invocation satisfies the agentic delegation requirement.
