# Orchestration generator

`generate.py` writes each AI client's Code Workflow orchestration on this computer from templates, following the orchestration decisions in [`docs/setup-design.md`](../docs/setup-design.md). The output depends only on the templates, the specialists installed in each client, the platform and the folder paths, so a second run changes nothing.

Built so far: **Claude Code**. Next: Codex, then GitHub Copilot with the VS Code helper extension, then Kiro and Antigravity. Clients without a template yet are detected and reported.

## Run it

```bash
python orchestration/generate.py --dry-run          # report what would change; write nothing
python orchestration/generate.py                    # write it
python orchestration/generate.py --replace-legacy   # first run on a computer where install.ps1 or install.sh was used
```

Use `python3` on macOS. The pack home is `~/.code-workflow`, or `CODE_WORKFLOW_HOME`; Claude Code's folder follows `CLAUDE_CONFIG_DIR` when it is set.

## What it writes

| Where | What |
|---|---|
| `~/.code-workflow/tooling/workflow.py`, `~/.code-workflow/hooks/claude_event.py` | The controller and hook script, installed once for every repository |
| `~/.code-workflow/tooling/agent-registry.yml` | The registry of installed specialists, refreshed after each run |
| `~/.code-workflow/hooks/claude-code.settings.json` | Claude Code's hook configuration, ready to merge but not turned on |
| `~/.claude/agents/agentic-orchestrator-anthropic-claude-code.md` | The orchestrator, listing the specialists installed in Claude Code |
| `~/.claude/skills/` | The six workflow skills |
| `~/.claude/rules/code-workflow.md` | A short rule that tells every Claude Code session the orchestrator exists |
| `~/.code-workflow/generated.json` | Every file written, with its sha256 |

## Safety rules

- A file is written only when it is new, or when this tool wrote it and nobody has changed it since.
- Anything else, such as a file you edited or one another tool wrote, stops that client and is reported. Nothing is written for that client.
- Files from the earlier per-repository installer are replaced only with `--replace-legacy`, after a copy is saved in `~/.code-workflow/backup/<time>/`.
- A file it no longer generates is removed only when it is unchanged.
- Hooks are written ready to use but never turned on.

To undo, delete the files listed in `~/.code-workflow/generated.json`, then copy back anything saved under `~/.code-workflow/backup/`.

## Using the Claude Code orchestrator

- `claude --agent agentic-orchestrator-anthropic-claude-code` makes it the session's main agent. It then loads the workflow skills when it needs them.
- In any Claude Code session, ask for the `agentic-orchestrator-anthropic-claude-code` agent. Run as a subagent, it starts with the six skills preloaded and can still delegate, because Claude Code lets subagents start their own, up to three levels deep.
- It delegates only to agents installed in Claude Code: every controller call passes `--client claude-code`.

## Layout

- `generate.py`: the generator. Standard library only, Python 3.8 or later.
- `templates/<client>/`: the templates for one client. Placeholders: `name`, `tools`, `skills`, `controller`, `pack_home`, `roster`.
- `skills/`: the six workflow skills, identical for every client. Their only placeholders are `controller` and `pack_home`.

## Verified

2026-10-18, Windows, Claude Code 2.1.302: generated into a real profile that had the earlier installer's files (backed up and replaced), then a one-agent workflow ran end to end in a scratch repository. The orchestrator created the workflow with `--client claude-code`, delegated to `terraform-expert-engineer` with the Agent tool, received its handoff, ran the gates, and `validate` reported the workflow `completed`.

Still to check by hand: the same orchestrator in the VS Code Claude Code panel, which runs its own bundled copy of Claude Code and reads the same `~/.claude` folder.
