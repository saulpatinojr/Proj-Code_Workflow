# Code Workflow

**Structured multi-agent workflows inside the AI assistant you already use.** One-script setup, no background runtime.

Code Workflow adds an orchestrator agent, six skills, a lifecycle hook, and a small Python workflow controller to **Claude Code**, **OpenAI Codex CLI**, and **GitHub Copilot** (CLI and VS Code), on **Windows** and **macOS/Linux**. The orchestrator delegates to your installed specialist agents through the client's own subagents. It requires a durable handoff from every specialist, runs deterministic checks, and reports a truthful completion state.

It is the slim sibling of [Code Conductor](https://github.com/saulpatinojr/Proj-Code_Conductor), the full cross-provider program.

## Boundaries

| | **Code Workflow** (this repo) | **Code Conductor** |
|---|---|---|
| Where coordination happens | Inside one AI client, through its native subagents | Across clients: launches Claude, Codex, Kiro and others and coordinates between them |
| Setup | `install.ps1` / `install.sh` plus Python 3.8+ | Node 22+, APM 0.30.0, Git, GitHub CLI, VS Code extension or `cc` CLI |
| Governance | Handoff contract, evidence hashing, deterministic gates, opt-in stop guard | Risk classes R0–R4, different-provider challengers, worktrees, blocking gates, human approval |
| Best for | One developer or one engagement that wants structured delegation today | Teams and client work needing independent multi-vendor review and an audit trail |

Code Workflow deliberately **never**:

- spawns another provider's CLI;
- manages git worktrees;
- issues merge or readiness decisions.

The test suite enforces these rules (`BoundaryTests`). The products share one result contract, Code Conductor's `RunManifest`/`AgentResult` (Code Conductor ADR 0011), so work can move up:

```bash
python3 tooling/workflow.py export --workflow <id>      # Code Workflow: writes run-manifest.json
cc import .agentic/workflows/<id>/run-manifest.json     # Code Conductor: brings it under governed review
```

## Install

1. Put your specialist agent packs in place in any ecosystem's folder: `~/.claude/agents`, `~/.copilot/agents`, `~/.codex/agents`, or the repository equivalents.
2. Run the installer from a clone of this repository:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\install.ps1     # Windows
   ```
   ```bash
   bash ./install.sh                                          # macOS / Linux
   ```

   You pick the clients. The installer copies the payloads (or verifies them, if you copied by hand), merges hook settings without overwriting yours, appends a marked section to `AGENTS.md`, and walks you through `registry`, `discover`, `init` (with a numbered agent picker), and `doctor`.
3. Invoke the agent:
   - **Claude Code:** `@agent-claude-agentic-orchestrator`, or `claude --agent claude-agentic-orchestrator`
   - **Copilot CLI:** `copilot --agent claude-agentic-orchestrator`
   - **VS Code Copilot:** the chat agent picker
   - **Codex:** ask for the orchestrator agent

[`PLACEMENT.md`](PLACEMENT.md) maps every file to its destination, lists every command, and explains how to uninstall.

## How a workflow runs

1. `workflow.py init` creates `.agentic/workflows/<id>/` **before** any delegation.
2. The orchestrator delegates each required node to a specialist subagent. Each specialist writes `.agentic/workflows/<id>/handoffs/<agent-id>.yml`.
3. `workflow.py gates` runs deterministic checks. Gate output is logged with a sha256, and gate results outrank any agent's opinion.
4. `workflow.py validate` checks every handoff:
   - evidence paths must be repository-relative and exist, and are hashed;
   - a `completed` handoff must cite a real file;
   - missing required agents block, and missing optional agents are skipped.
5. `workflow.py export` (optional) hands the record to Code Conductor.

Audit hooks log only an allowlisted set of event fields, never prompts, transcripts, or tool input/output. Logs land in `.agentic/audit/`, which `.agentic/.gitignore` keeps out of git.

## Development

```bash
python3 -m unittest discover -s tests -v
```

CI runs the suite on Windows, macOS, and Linux, plus `bash -n install.sh` and a PowerShell parser check of `install.ps1`. `tests/fixtures/code-conductor-contracts.schema.json` is a snapshot of Code Conductor's contract; refresh it whenever that schema changes.

## License

MIT. See [LICENSE](LICENSE).
