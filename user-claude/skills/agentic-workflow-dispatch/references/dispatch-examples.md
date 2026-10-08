# Dispatch Examples

Agent names below are examples; use the names in your generated `tooling/agent-registry.yml`.

## One agent

Use the smallest capable agent, for example a documentation agent for a documentation-only request. Create the workflow with one required node, invoke that exact specialist subagent, validate its handoff, then report.

## Selected agents

For a Terraform change requiring architecture and documentation, select the Terraform agent followed by the documentation agent. The documentation node depends on the Terraform node's findings and must receive its handoff path as an input.

## All available agents

Use `mode: all` only when the user asks for a broad cross-domain review. Discover installed agents first. Spawn independent reviewers in bounded parallel groups, then run a synthesis node only after all required handoffs are present. Uninstalled optional agents are recorded as skipped rather than treated as failures.
