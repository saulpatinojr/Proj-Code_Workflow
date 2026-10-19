# Changelog

## 0.1.0 (unreleased, pre-alpha)

Pre-alpha rebrand as **Code Workflow**, the slim, in-client sibling of Code Conductor. Previously distributed as the "claude-agentic-orchestrator" pack (v1 to v3.1).

### Added

- Roles, stances and independence in the orchestration (Code Conductor ADR 0015): `agentic-workflow-dispatch` gains `references/roles-and-stances.md`, the Manager, Judge and Auditor rules shared with Code Conductor's `config/roles.yaml`. The orchestrator classifies the work (R0 to R4) and plans the nodes from the class, names a stance (`constructive`, `critical`, `neutral`) in every delegation, never lets a node review its own output, rules between disagreeing handoffs by requirements and policy, then executable evidence, then official references, with the agents' confidence last, and reads a pull request's checks and reviews from GitHub before the summary. R3 and R4 work stops before any external side effect and is sent to Code Conductor. Handoffs may record `stance`. The orchestrator still never says a change is ready to merge; the Claude Code template carries the section, and a test keeps every template and skill free of a readiness verdict.
- `workflow.py gates`: deterministic Terraform, Ansible, npm, and pytest checks, plus custom profiles in `tooling/gates.json`. Output is logged with a sha256. A missing tool is recorded as `skipped`, never as passed. `init --require-gates` makes gates mandatory.
- Evidence integrity in `validate`:
  - cited evidence and artifact paths must be repository-relative, and paths escaping the repository are rejected;
  - existing files are hashed;
  - a `completed` handoff must cite at least one real file.
- Completion is bound to what was reviewed and checked:
  - a handoff's cited files must keep the content they had when the handoff was accepted, or the sha256 the handoff records; a file modified after the handoff was written blocks its first acceptance;
  - gate results record a fingerprint of the repository's content outside `.agentic/`, and become stale, blocking validation and marked in the export, when that content changes;
  - a node takes the status its agent reported, so a handoff that reports `blocked` or a failure no longer completes the workflow.
- `workflow.py export`: writes `run-manifest.json` in Code Conductor's `RunManifest`/`AgentResult` shape, including `notVerified`. It never recommends `ready` and never writes a merge decision. Use `cc import` on the Code Conductor side.
- `workflow.py doctor`: install health check covering clients, skills, hooks, registry freshness, and the `.agentic/.gitignore`.
- `init --risk R0..R4` and `--acceptance "a; b"`, both carried into the export.
- `--version`; workflow ids are validated to prevent path traversal.
- A stdlib `unittest` suite covering lifecycle, gates, evidence, export contract, hook redaction, the stop guard, doctor, product-boundary guards, and pack integrity. CI runs on Windows, macOS, and Linux.
- README, CHANGELOG, LICENSE, and an uninstall section in PLACEMENT.md.
- `orchestration/generate.py`: generates each client's orchestration in the user profile from templates. The first template is Claude Code: the orchestrator `agentic-orchestrator-anthropic-claude-code` (listing the specialists installed in Claude Code), six client-neutral workflow skills, a short rule, and hook configuration that is written but not turned on. The controller and hook are installed once in `~/.code-workflow/`. The generator is deterministic, records every file it writes with its sha256, never overwrites a file it did not write or that was changed since, and replaces the earlier installer's files only with `--replace-legacy`, after a backup. See `orchestration/README.md`.
- `discover --client` and `init --client`: an orchestrator counts only the agents its own client can run; the client is recorded in `WORKFLOW.json`.

### Changed

- The audit hook now records only allowlisted event fields: prompts, transcripts, assistant messages, and tool input/output are dropped. It creates `.agentic/.gitignore` so audit logs stay out of git.
- The handoff parser now reads the full contract (lists of mappings, `not_verified`) instead of line regexes, and status values are validated.
- The installers are rebranded and offer `doctor` at the end of the guided run.
- Agent discovery follows `CLAUDE_CONFIG_DIR`, `COPILOT_HOME` and `CODEX_HOME`, and treats every `agentic-orchestrator-*` agent, like the earlier `claude-agentic-orchestrator`, as an orchestrator rather than a specialist.
- Custom gates come from the repository's own `tooling/gates.json` first, so a controller installed once in the profile still runs each repository's checks.
- The Stop guard also finds the controller beside the hook's own pack home, and its message names the controller's real path.
- The two Claude-named skills are client-neutral in the generated orchestration: `subagent-delegation` and `workflow-hooks-and-guardrails`.

### Fixed

- The registry reads agent descriptions that wrap over several lines in the file header, and trims long ones at a word boundary instead of mid-word.
- `install.ps1` writes `settings.json` without a byte-order mark. Both installers leave `settings.json` untouched when every hook entry is already present.
- Both installers keep the first `settings.json.backup-orchestrator`, so a re-run no longer replaces the backup of your original settings.
- A re-run no longer offers to overwrite the generated `tooling/agent-registry.yml`.
- `doctor` says when hooks or the AGENTS.md section are absent, instead of printing the "present" wording at INFO level.

### Carried forward from 3.1 (re-verified against client docs 2026-10-08)

- Client adapters for Claude Code (`.md`), Codex (`.toml`), and Copilot (`.agent.md`), with shared SKILL.md skills.
- Multi-ecosystem agent discovery into one registry.
- Fail-open, opt-in stop guard; JSON output from Stop/SubagentStop for Codex's strict validation.
- Interactive Windows and macOS/Linux installers with client selection, VERIFY MODE, idempotent hook merge, and AGENTS.md section.
