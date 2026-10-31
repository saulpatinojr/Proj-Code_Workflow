# Orchestration generator

`generate.py` writes each AI client's Code Workflow orchestration on this computer from templates, following the orchestration decisions in [`docs/setup-design.md`](../docs/setup-design.md). The output depends only on the templates, the specialists installed in each client, the platform and the folder paths, so a second run changes nothing.

Built so far: **Claude Code**, **GitHub Copilot** (Copilot CLI, the GitHub Copilot app and VS Code's Copilot harness) and **OpenAI Codex** (Codex CLI, its VS Code extension and the ChatGPT desktop app). Next: the VS Code helper extension, then Kiro and Antigravity. Clients without a template yet are detected and reported.

## Run it

```bash
python orchestration/generate.py --dry-run          # report what would change; write nothing
python orchestration/generate.py                    # write it
python orchestration/generate.py --replace-legacy   # first run on a computer where install.ps1 or install.sh was used
```

Use `python3` on macOS. Add `--client claude-code`, `--client github-copilot` or `--client codex` (repeatable) to generate for chosen clients only; by default every detected client is generated. The pack home is `~/.code-workflow`, or `CODE_WORKFLOW_HOME`; each client's folder follows its own variable when it is set: `CLAUDE_CONFIG_DIR`, `COPILOT_HOME`, `CODEX_HOME`.

## What it writes

| Where | What |
|---|---|
| `~/.code-workflow/tooling/workflow.py`, `~/.code-workflow/hooks/claude_event.py` | The controller and hook script, installed once for every repository |
| `~/.code-workflow/tooling/agent-registry.yml` | The registry of installed specialists, refreshed after each run |
| `~/.code-workflow/hooks/claude-code.settings.json` | Claude Code's hook configuration, ready to merge but not turned on |
| `~/.claude/agents/agentic-orchestrator-anthropic-claude-code.md` | The orchestrator, listing the specialists installed in Claude Code |
| `~/.claude/skills/` | The six workflow skills |
| `~/.claude/rules/code-workflow.md` | A short rule that tells every Claude Code session the orchestrator exists |
| `~/.copilot/agents/agentic-orchestrator-github-copilot.agent.md` | Copilot's orchestrator, listing the specialists installed in Copilot |
| `~/.copilot/instructions/code-workflow.instructions.md` | Instructions (`applyTo: "**"`) that tell every Copilot session the orchestrator exists |
| `~/.codex/agents/agentic-orchestrator-openai-codex.toml` | Codex's orchestrator, listing the specialists installed in Codex |
| `~/.agents/skills/` | The six workflow skills, one copy shared by Copilot and Codex. When `COPILOT_HOME` is set, Copilot gets its own copy in `$COPILOT_HOME/skills/`, because Copilot CLI then stops reading `~/.agents/skills` |
| `~/.code-workflow/hooks/github-copilot.hooks.json`, `~/.code-workflow/hooks/codex.hooks.json` | Copilot's and Codex's hook files, ready to copy into `~/.copilot/hooks/` or `~/.codex/hooks.json` but not turned on |
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

## Using the GitHub Copilot orchestrator

- **GitHub Copilot app:** pick `agentic-orchestrator-github-copilot` in the agent picker, or type `/agent` in a session. The app reads `~/.copilot/agents` and the skills configured for Copilot CLI.
- **Copilot CLI:** `copilot --agent agentic-orchestrator-github-copilot`, or `/agent` in a session.
- **VS Code:** pick it in the chat agent dropdown. VS Code's Copilot harness reads `~/.copilot/agents` only when `github.copilot.chat.cli.customAgents.enabled` is on, and that setting defaults to off.
- It delegates with Copilot's `agent` tool, only to agents installed in Copilot: every controller call passes `--client github-copilot`. `include-custom-instructions: true` lets it read the repository's `AGENTS.md` when it runs as a subagent.

## Using the Codex orchestrator

- Start `codex` (or the Codex view in VS Code or the ChatGPT desktop app) and ask for the `agentic-orchestrator-openai-codex` agent; Codex spawns subagents when asked to delegate.
- It delegates only to agents installed in Codex: every controller call passes `--client codex`.
- Not generated yet: a marked section in `~/.codex/AGENTS.md` telling every Codex session the orchestrator exists (decision "Instructions" in `docs/setup-design.md`). It needs a merge into the user's own file, which the whole-file write rules here do not cover.

## Layout

- `generate.py`: the command. It detects clients, runs each client's planner and reports. Standard library only, Python 3.8 or later.
- `safe_files.py`: the write rules above, in one place.
- `common.py`: helpers shared by the planners, such as rendering, the skills and the controller command.
- `claude_code.py`, `github_copilot.py`, `codex.py`: one planner per client. Each further client gets its own module beside them and its own templates folder.
- `templates/<client>/`: the templates for one client. Placeholders: `name`, `tools`, `skills`, `controller`, `pack_home`, `roster`. Codex's agent is TOML with the instructions in one `'''` literal string, so the rendered instructions may not contain `'''`; the planner refuses to write one that does.
- `skills/`: the six workflow skills, identical for every client. Their only placeholders are `controller` and `pack_home`.

## Verified

2026-10-18, Windows, Claude Code 2.1.302: generated into a real profile that had the earlier installer's files (backed up and replaced), then a one-agent workflow ran end to end in a scratch repository. The orchestrator created the workflow with `--client claude-code`, delegated to `terraform-expert-engineer` with the Agent tool, received its handoff, ran the gates, and `validate` reported the workflow `completed`.

Still to check by hand: the same orchestrator in the VS Code Claude Code panel, which runs its own bundled copy of Claude Code and reads the same `~/.claude` folder.
