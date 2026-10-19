# Roles, stances and independence

The specialists come from the packs installed in this client; they are the experts. What
this reference adds is the orchestration layer around them: the stance each node takes,
how many nodes a piece of work needs, who may judge whom, and how the orchestrator rules
when handoffs disagree. These rules are shared with Code Conductor (its `config/roles.yaml`,
ADR 0015), so a workflow exported with `{{controller}} export` reads the same way there.

## Stances

Every delegation names one stance, and the handoff records it as `stance:`.

| Stance | Means | Typical nodes |
|---|---|---|
| `constructive` | Build, improve, solve, optimize. | The specialist that makes the change. |
| `critical` | Challenge, find defects, identify risks, try to falsify assumptions. | A review node, a challenger node. |
| `neutral` | Research, measure, validate, compare. | A research node, a gate run, a ruling between two handoffs. |

A critical node must give evidence for each material objection and must say so when the
work withstands the challenge. Manufactured disagreement is a defect of the review, not a
sign of independence.

## How many nodes the work needs

Classify the work before `init`, and plan the nodes from the class. This client cannot run a
second provider, so the unit of independence here is a **different agent**: the node that
reviews is never the node that built.

| Class | Work | Nodes |
|---|---|---|
| R0 | Trivial, bounded, low impact. | One constructive node, then gates. |
| R1 | A normal engineering change. | One constructive node, one critical review node by a different agent, then gates. |
| R2 | Important or cross-component. | R1 plus a critical challenger node that tries to falsify the change, and the GitHub check below when a pull request exists. |
| R3, R4 | High impact, security, production, destructive or externally consequential. | Not this product. Record the class in the summary, stop before any external side effect, and tell the user the work belongs in Code Conductor (`{{controller}} export` carries what was done). |

When the client has no second agent that can review the change, the review node is
`blocked`, not skipped: say which pack would provide it.

## Independence

- A node never reviews its own output, and a constructive node never marks its own work
  reviewed.
- The orchestrator never writes or edits a specialist's handoff. It may summarize one; it
  may not make an incomplete result look complete.
- A review node is read-only. When it finds a defect, the fix goes back to a constructive
  node and the review runs again on the new result.
- Gate results outrank every handoff, including the orchestrator's own reading of them.

## Ruling between handoffs (the orchestrator as arbiter)

When two handoffs disagree on a material point, the orchestrator rules, in this order of
authority, and records the ruling in the summary:

1. the user's requirements and the repository's policy;
2. executable evidence: gate output, test results, a reproduction;
3. official vendor documentation and other authoritative references;
4. safety and maintainability;
5. the agents' own confidence, last. A stronger model does not win by being stronger.

State which claim is accepted, which is rejected and which stays unresolved, and why. When
evidence cannot safely settle a consequential conflict, leave it unresolved and escalate to
the user instead of choosing.

## The GitHub check (the orchestrator as gatekeeper)

When the change has a pull request, read its state from GitHub before the summary, with
the GitHub CLI the user is signed in to (`gh pr view`, `gh pr checks`): required checks,
review findings, unresolved conversations and the branch state. GitHub is the source of
truth for that state; a local diff is not. A failing or missing required check, or an
unresolved blocking review finding, is reported as blocking the workflow and named in the
summary. The orchestrator never approves or merges, and never asks a specialist to.

## What stays with Code Conductor

Readiness and merge decisions, a different-provider challenger, isolated worktrees for
every modifying node, and pre-action approvals bound to the exact change. A Code Workflow
summary reports the workflow's status and the evidence; it never says the change is ready
to merge. `{{controller}} export` hands the record to Code Conductor for that decision.
