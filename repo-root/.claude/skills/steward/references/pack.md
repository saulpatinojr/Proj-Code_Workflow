# Mode: pack

Keep an agent pack valid across Claude Code, Codex, and GitHub Copilot. Applies to any repository that ships or installs agents and skills, including Code Workflow itself.

## Checks

| Area | How to check | Fix on the branch? |
|---|---|---|
| Skill frontmatter | Every `*/skills/<name>/SKILL.md` starts with `---`, then `name:` equal to its folder name (lowercase, digits, hyphens), then `description:` of at most 1024 characters, then `---` | Yes |
| Skill links | Every `](references/...)` link in a SKILL.md resolves to a file in that skill folder | Yes: fix the link or add the missing reference |
| Claude agents | `.claude/agents/*.md` and `user-claude/agents/*.md` have frontmatter with `name` and `description`; every name in `skills:` exists as a skill folder that installs alongside it | Yes |
| Codex agents | `*.toml` parses and has exactly `name`, `description`, `developer_instructions` | Yes |
| Copilot agents | `*.agent.md` has `name` and `description` frontmatter | Yes |
| Cross-client contract | The same agent's Claude, Codex, and Copilot definitions carry the same contract phrases (for the orchestrator: `workflow.py init`, `workflow.py gates`, `validate`, `handoffs/<agent-id>.yml`) | Yes: align the lagging adapter |
| Registry | Run `python tooling/workflow.py registry` in a scratch copy and diff against `tooling/agent-registry.yml`; `workflow.py doctor` reports registry freshness | Yes: regenerate; never hand-add an agent that is not installed |
| Placement | Every payload file appears in `PLACEMENT.md` (or its folder does), payload folders mirror their install destination, and both installers copy every payload folder | Yes |
| Installer parity | Every copy step in `install.sh` has a matching step in `install.ps1`, and the reverse | Yes |
| Boundaries | No agent, skill, or template says a change is ready to merge, starts another vendor's AI CLI, or manages git worktrees | Yes: remove the wording |
| Changelog | User-visible pack changes since the last release have a `CHANGELOG.md` entry | Yes |

## Verify

Run the pack's tests (for Code Workflow: `python3 -m unittest discover -s tests -v` and `bash -n install.sh`). Never run an installer for real while testing; it writes into the home folder.

## Done when

Every row has a result, the tests pass after the last commit, and the findings table lists anything left for the owner.
