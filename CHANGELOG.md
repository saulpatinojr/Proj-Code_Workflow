# Changelog

## 1.0.0 (2026-10-08)

First release as **Code Workflow**, the slim, in-client sibling of Code Conductor. Previously distributed as the "claude-agentic-orchestrator" pack (v1 to v3.1).

### Added

- `workflow.py gates`: deterministic Terraform, Ansible, npm, and pytest checks, plus custom profiles in `tooling/gates.json`. Output is logged with a sha256. A missing tool is recorded as `skipped`, never as passed. `init --require-gates` makes gates mandatory.
- Evidence integrity in `validate`:
  - cited evidence and artifact paths must be repository-relative, and paths escaping the repository are rejected;
  - existing files are hashed;
  - a `completed` handoff must cite at least one real file.
- `workflow.py export`: writes `run-manifest.json` in Code Conductor's `RunManifest`/`AgentResult` shape, including `notVerified`. It never recommends `ready` and never writes a merge decision. Use `cc import` on the Code Conductor side.
- `workflow.py doctor`: install health check covering clients, skills, hooks, registry freshness, and the `.agentic/.gitignore`.
- `init --risk R0..R4` and `--acceptance "a; b"`, both carried into the export.
- `--version`; workflow ids are validated to prevent path traversal.
- A stdlib `unittest` suite covering lifecycle, gates, evidence, export contract, hook redaction, the stop guard, doctor, product-boundary guards, and pack integrity. CI runs on Windows, macOS, and Linux.
- README, CHANGELOG, LICENSE, and an uninstall section in PLACEMENT.md.

### Changed

- The audit hook now records only allowlisted event fields: prompts, transcripts, assistant messages, and tool input/output are dropped. It creates `.agentic/.gitignore` so audit logs stay out of git.
- The handoff parser now reads the full contract (lists of mappings, `not_verified`) instead of line regexes, and status values are validated.
- The installers are rebranded and offer `doctor` at the end of the guided run.

### Carried forward from 3.1 (re-verified against client docs 2026-10-08)

- Client adapters for Claude Code (`.md`), Codex (`.toml`), and Copilot (`.agent.md`), with shared SKILL.md skills.
- Multi-ecosystem agent discovery into one registry.
- Fail-open, opt-in stop guard; JSON output from Stop/SubagentStop for Codex's strict validation.
- Interactive Windows and macOS/Linux installers with client selection, VERIFY MODE, idempotent hook merge, and AGENTS.md section.
