# Dispatch examples

The agent names below are examples. Use the names that `{{controller}} discover --client <client>` reports.

## One agent

Use the smallest capable agent, for example a documentation agent for a documentation-only request. Create the workflow with one required node, invoke that exact specialist, validate its handoff, then report.

## Selected agents

For a Terraform change that needs architecture and documentation, select the Terraform agent, then the documentation agent. The documentation node depends on the Terraform node's findings and receives its handoff path as an input.

## All available agents

Use `--mode all` only when the user asks for a broad cross-domain review. Discover first. Start independent reviewers in bounded parallel groups, and run a synthesis step only after every required handoff is present. Agents your client cannot run are recorded as skipped, not treated as failures.
