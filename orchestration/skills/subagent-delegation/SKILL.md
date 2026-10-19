---
name: subagent-delegation
description: Hand a workflow node to a specialist subagent with an explicit prompt, scoped context, dependency handoffs and clear permission limits.
---

Use this skill when the orchestrator is ready to dispatch a registered specialist.

Use your client's own subagent mechanism and the exact agent name that discovery reported. The delegation prompt must include:

- the workflow ID and agent ID;
- the node's stance, `constructive`, `critical` or `neutral`, and what it means for this node (a critical node gives evidence for each objection and says when the work holds up);
- the objective and acceptance criteria;
- the files or evidence in scope;
- dependencies and the paths of earlier handoffs;
- the required handoff path, `.agentic/workflows/<workflow-id>/handoffs/<agent-id>.yml`;
- the authorization boundary and the actions it must not take;
- an instruction to write the structured handoff before it responds.

The orchestrator stays responsible for routing and for the final summary. Do not ask a specialist to start another specialist; nested delegation cannot be assumed. Never give a review node its own earlier output to review: the node that reviews is a different agent from the node that built. Run independent nodes in bounded parallel groups and dependent nodes in order.

Use an isolated worktree only when a node is expected to edit files and the workflow explicitly wants a separate change set. Never use a permission-bypass mode just to make delegation appear to succeed.
