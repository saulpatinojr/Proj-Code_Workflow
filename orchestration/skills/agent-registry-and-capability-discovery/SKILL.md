---
name: agent-registry-and-capability-discovery
description: Find the specialist agents installed for your client and map them to capabilities, required or optional workflow nodes, and exact invocation names.
---

Use this skill before dispatch when the user asks for any, all, available, installed or the best agent, or when the role you need is not known.

The registry, `agent-registry.yml`, lives beside the controller and is generated from the installed agents by `{{controller}} registry`. It scans every client's agent folders, in the repository and in the user profile, and records which clients carry each agent. Regenerate it whenever agents are installed or removed, and never hand-write agent names that are not installed.

Then run `{{controller}} discover --client <client>`. With `--client`, an agent counts as available only when your client can run it, because an orchestrator delegates only to agents installed in its own client. Discovery always reads the folders fresh, so a newly installed agent is never hidden.

Classify each node you need:

- `available`: an agent your client can run provides the capability.
- `optional-unavailable`: no such agent, and the workflow can do without it.
- `required-unavailable`: no such agent, and the workflow needs it. Tell the user which agent pack to install.
- `ambiguous`: more than one agent claims the capability; choose explicitly.

A skill is not an agent. Skills provide knowledge and procedures; only a real subagent invocation satisfies a delegation requirement.
