# Code Workflow: where everything goes, and why (three clients, two platforms)

One pack, three clients (Claude Code, OpenAI Codex CLI, GitHub Copilot), two platforms (Windows, macOS/Linux). The payload folders **mirror their destinations**, so drag-and-drop is a straight copy. The installers do the copying, verifying, and merging — `install.ps1` on Windows, `install.sh` on macOS/Linux — and both let you pick which clients to install. Formats re-verified against official client docs 2026-10-08.

```text
Proj-Code_Workflow\  (repository root = the pack)
├── install.ps1          <- Windows installer (interactive, client picker)
├── install.sh           <- macOS / Linux installer (interactive, client picker)
├── PLACEMENT.md         <- this file
├── README.md / CHANGELOG.md / LICENSE
├── tests\  .github\       <- repository CI only; never installed
│
├── user-claude\         ==> ~/.claude\                (Claude Code: agent + 6 skills)
│   ├── agents\claude-agentic-orchestrator.md
│   └── skills\<6 skills>\
│
├── user-codex\          ==> ~/.codex\                 (Codex CLI)
│   └── agents\claude-agentic-orchestrator.toml
│
├── user-copilot\        ==> ~/.copilot\               (GitHub Copilot, CLI + VS Code)
│   └── agents\claude-agentic-orchestrator.agent.md
│
└── repo-root\           ==> <your-repository>\
    ├── .claude\settings.agentic-orchestrator.json     <- merged into .claude\settings.json
    ├── .codex\hooks.sample.json                       <- rename to hooks.json, then trust via /hooks in Codex
    ├── .github\hooks\agentic-orchestrator.sample.json <- Copilot CLI hooks; rename after review
    ├── AGENTS-orchestrator.md                         <- appended into AGENTS.md (marker-guarded)
    ├── hooks\claude_event.py                          <- one hook script for all three clients
    └── tooling\workflow.py + agent-registry.yml   (+ optional gates.json you add)
```

Created at runtime in your repository (not shipped): `.agentic\` with workflow records, gate evidence logs, the redacted audit log, and its own `.gitignore`. `workflows\` is committable evidence; `audit\`, `discovery.json`, and `active-workflow.json` stay machine-local.

## Two kinds of adapters

**Client adapters** (how each AI invokes the orchestrator): the skills, hook script, and workflow controller are shared — all three clients converged on the open SKILL.md standard and JSON-on-stdin hooks, and Copilot reads Claude-format files natively. Only the orchestrator agent definition is per-client, because each client has its own dialect (markdown frontmatter, TOML, .agent.md).

**Agent-pack adapters** (how the harness sees YOUR specialists): `workflow.py` discovery scans every installed ecosystem and merges them into one registry —

| Ecosystem | Repo scope | User scope | Format |
|---|---|---|---|
| claude-code | `.claude/agents/` | `~/.claude/agents/` | `*.md`, frontmatter `name` |
| github-copilot | `.github/agents/` | `~/.copilot/agents/` | `*.agent.md` / `*.md` |
| codex | `.codex/agents/` | `~/.codex/agents/` | `*.toml`, `name = "..."` |

Each registry entry records which clients carry the agent, so a mixed estate — Claude-format domain agents plus a vendor's Copilot agent pack plus a Codex TOML pack — lands in one capability index. Drop any pack into its native folder and re-run `workflow.py registry`; nothing needs converting.

## Placement matrix

| Component | Claude Code | Codex CLI | GitHub Copilot |
|---|---|---|---|
| Orchestrator agent | `~/.claude/agents/*.md` | `~/.codex/agents/*.toml` | `~/.copilot/agents/*.agent.md` (CLI + VS Code) |
| The 6 skills | `~/.claude/skills/` | `~/.agents/skills/` (shared standard) | same `~/.agents/skills/` copy; VS Code also reads `~/.claude/skills/` |
| Repo instructions | agent picks them up | `AGENTS.md` section | `AGENTS.md` section |
| Hooks (audit + stop guard) | `.claude/settings.json` merge | `.codex/hooks.json` (from sample; must be trusted via `/hooks`) | CLI: `.github/hooks/*.json` (from sample). VS Code: reads the Claude settings hooks **only when `chat.useClaudeHooks` is enabled** (off by default) |
| Workflow state + tooling | `<repo>/tooling/`, `<repo>/.agentic/` | same | same |

## Windows vs macOS commands

`workflow.py` and `claude_event.py` are OS-neutral. The only difference is the interpreter name: **Windows = `python`** (or `py -3`), **macOS/Linux = `python3`**. Each installer writes hook commands with the right interpreter for its OS at merge time. If a repo's settings file is shared across both OSes by git, pick one convention for the team.

## Hook samples ship disabled — why

The Claude hook merge is exact and tested. Codex and Copilot-CLI hooks ship as `.sample.json` because activating them is a deliberate act in both clients anyway: Codex only runs hooks after you review and **trust** them via `/hooks` (hash-pinned; project hooks only in trusted projects), and Copilot's format is newer. Rename to `.codex/hooks.json` / `.github/hooks/agentic-orchestrator.json` to activate. They are audit-only (event log in `.agentic/audit/`); the workflow's correctness never depends on them. The hook script always emits a JSON object from Stop/SubagentStop because Codex validates hook output strictly.

## Install order

1. Put your domain agent packs in place first — any ecosystem's folder works — so the generated registry includes them.
2. Run the installer for your OS from this folder:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\install.ps1     # Windows
   ```
   ```bash
   bash ./install.sh                                          # macOS / Linux
   ```

   Both: pick clients -> copy (or VERIFY MODE when you copied manually) -> merge hooks -> append AGENTS.md section -> guided `registry` / `discover` / `init` with a numbered agent picker.
3. Invoke per client:
   - **Claude Code**: new session from repo root -> `@agent-claude-agentic-orchestrator` in the prompt, or `claude --agent claude-agentic-orchestrator`
   - **Codex CLI**: `codex`, then ask for the orchestrator agent; subagents spawn when you ask it to delegate
   - **Copilot CLI**: `copilot --agent claude-agentic-orchestrator`; **VS Code**: pick the agent in the chat agent dropdown

## Workflow commands

All commands run from inside the repository. Use `python3` on macOS/Linux and `python` on Windows.

| Command | What it does |
|---|---|
| `workflow.py registry` | Regenerate the registry from installed agents across all three ecosystems |
| `workflow.py discover` | Show which registry agents are installed, where, and for which clients |
| `workflow.py init --mode one\|selected\|all --objective "..." [--risk R0-R4] [--acceptance "a; b"] [--require-gates] [--enforce-stop]` | Create the workflow record before delegating |
| `workflow.py gates --workflow <id>` | Run deterministic checks (Terraform, Ansible, npm, pytest, or custom `tooling/gates.json`); output logged with sha256 |
| `workflow.py validate --workflow <id> [--check]` | Validate handoffs, evidence paths and hashes, and gates |
| `workflow.py export --workflow <id>` | Write `run-manifest.json` in Code Conductor's `RunManifest` shape; bring it under Code Conductor review with `cc import` |
| `workflow.py doctor` | Check install health: clients, skills, hooks, registry freshness, gitignore |

Custom gates go in `tooling/gates.json`, for example: `{"disable": ["node"], "profiles": {"bicep": {"detect": {"any_suffix": [".bicep"]}, "gates": [{"id": "bicep-build", "command": ["az", "bicep", "build", "--file", "main.bicep"]}]}}}`. A missing tool is recorded as `skipped`, never silently passed. With `--require-gates`, a skipped blocking gate blocks validation.

## Uninstall

Remove `claude-agentic-orchestrator.*` from `~/.claude/agents`, `~/.codex/agents`, and `~/.copilot/agents`, and the six skill folders from `~/.claude/skills` and `~/.agents/skills`. In the repository:

- delete `tooling\` and `hooks\`;
- remove the four `claude_event.py` entries from `.claude/settings.json`; the backup taken before the first install is in `settings.json.backup-orchestrator`;
- delete the marked `BEGIN/END claude-agentic-orchestrator` block from `AGENTS.md`.

`.agentic\` holds your workflow evidence, so keep or delete it deliberately.

## Two rules that prevent every path problem

1. `workflow.py` resolves the repo as `--root` flag → `CLAUDE_PROJECT_DIR` env → git toplevel → current directory; its registry always resolves beside the script itself. Nesting cannot break it.
2. The Stop-guard is **opt-in** (`init --enforce-stop`) and **fail-open**; the block decision is honored by Claude Code and Codex, audit-only in Copilot. A mislocated install never traps a session in any client.
