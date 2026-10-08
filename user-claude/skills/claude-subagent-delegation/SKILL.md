---
name: claude-subagent-delegation
description: Invoke specialist subagents with explicit prompts, scoped context, dependency handoffs, and permission-aware delegation.
---

Use this Skill when the orchestrator is ready to dispatch a registered specialist agent.

Use the client's native subagent mechanism and the exact `agent_name` from the registry. The delegation prompt must include:

- workflow ID and agent ID;
- objective and acceptance criteria;
- files or evidence in scope;
- dependencies and prior handoff paths;
- required output path;
- authorization boundary and prohibited actions;
- instruction to write the structured handoff before responding.

The parent remains responsible for routing and final synthesis. Do not ask a domain subagent to spawn another domain subagent; recursive delegation cannot be assumed. Prefer bounded parallelism for independent nodes and sequential execution for dependent nodes.

Use isolated worktrees only when the node is expected to edit files and the workflow explicitly wants an isolated change set. Never use permission-bypass modes merely to make delegation appear successful.
