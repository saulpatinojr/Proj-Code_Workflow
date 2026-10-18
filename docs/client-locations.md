# Client locations

Verified 2026-10-18 against each vendor's official documentation.

This file records where each targeted AI client reads **user-level** configuration, meaning configuration that applies in every repository on the machine. It is the reference the installer must follow. Vendors moved several of these paths during 2026, so re-verify before changing the installer, and update the date above.

`~` means the user profile: `%USERPROFILE%` on Windows, `$HOME` on macOS and Linux.

## Versions checked

| Client | What the docs reflect | Installed on the reference machine |
|---|---|---|
| Claude Code | Docs and changelog through 2.1.302 | 2.1.292 |
| OpenAI Codex CLI | Release rust-v0.163.0 (2026-10-15) | 0.163.0 |
| GitHub Copilot CLI | Changelog through 1.0.98 (2026-10-14) | Not installed |
| VS Code with GitHub Copilot | Docs dated 2026-10-14 (VS Code 1.142) | 1.142.0 |
| Kiro (AWS) | IDE 1.3.11 (2026-10-15), CLI 2.31.1 (2026-10-14); CLI 3.0 due end of October 2026 | Not installed |
| Gemini CLI | v0.64.0 (2026-10-13). Unpaid and Google One users were moved to Antigravity CLI on 2026-06-18 | Not installed |

## Agents

| Client | User-level location | Format | Notes |
|---|---|---|---|
| Claude Code | `~/.claude/agents/*.md` | Markdown with YAML frontmatter. `name` and `description` are required. | Same name in several places: managed, then `--agents` flag, then project, then user, then plugin. |
| Codex CLI | `~/.codex/agents/*.toml` | TOML. `name`, `description`, `developer_instructions` are required. | Markdown agents are not read. Agent files may not set `sandbox_mode`, `approval_policy`, `model_provider`, or `mcp_servers`. |
| Copilot CLI | `~/.copilot/agents/*.agent.md` | Markdown with frontmatter. `description` is required. | Since 1.0.36 the CLI no longer reads anything from `~/.claude/`. |
| Kiro | `~/.kiro/agents/<name>.md` or `.json` | Markdown with frontmatter, or JSON. No field is required; `name` defaults to the file name. Common fields: name, description, prompt, tools, permissions, resources, model. | Workspace agents win over user agents of the same name. Docs disagree on whether custom agents inherit steering files by default; test on the target build. |
| Gemini CLI | `~/.gemini/agents/*.md` | Markdown. Frontmatter is mandatory; `name` and `description` are required. Optional: kind, tools, mcpServers, model, temperature, max_turns, timeout_mins. | Marked experimental. Invoked with `@name`. |
| VS Code | `~/.copilot/agents/` for Copilot sessions, `~/.claude/agents/` for Claude sessions | `.agent.md`, or Claude-format `.md` | Copilot-harness sessions may need `github.copilot.chat.cli.customAgents.enabled`, which defaults to false. Test this. |

## Skills

| Client | User-level location | Notes |
|---|---|---|
| Claude Code | `~/.claude/skills/<name>/SKILL.md` | Personal skills win over project skills. Plugin skills are namespaced as `plugin:skill`. Unknown frontmatter keys are ignored silently. |
| Codex CLI | `~/.agents/skills/<name>/SKILL.md` | `~/.codex/skills` is deprecated. This path follows `$HOME`, not `CODEX_HOME`. |
| Copilot CLI | `~/.copilot/skills/` and `~/.agents/skills/` | `~/.agents/skills` stops being read when `COPILOT_HOME` or `--config-dir` is set (1.0.66). Name up to 64 characters, description up to 1024. |
| Kiro | `~/.kiro/skills/<name>/SKILL.md` | Agent Skills standard. `name` must match the folder. |
| Gemini CLI | `~/.gemini/skills/<name>/SKILL.md` or `~/.agents/skills/` | The `.agents/skills` alias takes precedence over `.gemini/skills`. |
| VS Code | `~/.copilot/skills/`, `~/.claude/skills/`, `~/.agents/skills/` | The skill name must match its folder name. `chat.agentSkillsLocations` is deprecated. |

## Instructions that apply to every repository

| Client | User-level location | Notes |
|---|---|---|
| Claude Code | `~/.claude/CLAUDE.md` and `~/.claude/rules/*.md` | There is no user-level AGENTS.md. A separate rules file avoids editing the user's own CLAUDE.md. |
| Codex CLI | `~/.codex/AGENTS.md` | If `~/.codex/AGENTS.override.md` exists it replaces the base file, so the installer must never create it. |
| Copilot CLI | `~/.copilot/copilot-instructions.md` and `~/.copilot/instructions/**/*.instructions.md` | AGENTS.md is read only from the git root and current folder. Subagents skip it unless the agent sets `include-custom-instructions: true`. |
| Kiro | `~/.kiro/steering/*.md` | Optional frontmatter `inclusion: always`, `fileMatch` (needs `fileMatchPattern`), `manual`, or `auto` (needs `name` and `description`). An AGENTS.md there is always included. |
| Gemini CLI | `~/.gemini/GEMINI.md` | Plain Markdown with `@file.md` imports. Applies to all projects. |
| VS Code | The same `~/.copilot/` files. Claude sessions read `~/.claude/CLAUDE.md` and `~/.claude/rules/`. | `chat.useAgentsMdFile` defaults to true. |

## Hooks

| Client | User-level location | Notes |
|---|---|---|
| Claude Code | `hooks` key in `~/.claude/settings.json` | On Windows, commands run in Git Bash when it is installed, otherwise PowerShell. `${CLAUDE_PROJECT_DIR}` is the repository being worked on, so it cannot point at the pack. |
| Codex CLI | `~/.codex/hooks.json`, or `[hooks]` in `~/.codex/config.toml`, never both | Each hook runs only after the user trusts it once with `/hooks`, and again after any edit. Supports a `commandWindows` field. |
| Copilot CLI | `~/.copilot/hooks/*.json` | `version` is optional since 1.0.5. `timeout` is accepted for `timeoutSec`. The CLI also reads a repository's `.claude/settings.json`. |
| Kiro | `~/.kiro/hooks/*.json` (CLI V3 only) | JSON with `version: "v1"` and a `hooks` list of name, trigger, optional matcher, and action (command or agent). Triggers include PromptSubmit, Stop, SessionStart, SessionEnd, PreToolUse, PostToolUse, file events, and task events. Global hooks in the IDE are undocumented. |
| Gemini CLI | `hooks` key in `~/.gemini/settings.json` | Events: SessionStart, SessionEnd, BeforeAgent, AfterAgent, BeforeModel, AfterModel, BeforeToolSelection, BeforeTool, AfterTool, PreCompress, Notification. |
| VS Code | `~/.copilot/hooks/*.json` | Claude hook files are read only when `chat.useClaudeHooks` is on, which is off by default in Local sessions. |

## Relocating the configuration folder

- `CLAUDE_CONFIG_DIR` moves every `~/.claude` path.
- `CODEX_HOME` moves `~/.codex`. The folder must already exist. Codex inside WSL uses the Linux home unless `CODEX_HOME` points at the Windows one.
- `COPILOT_HOME` replaces `~/.copilot` and disables `~/.agents/skills` for the CLI.
- `KIRO_HOME` moves the Kiro CLI's global configuration (V3). IDE support is undocumented.
- `GEMINI_CLI_HOME` sets the folder in which Gemini CLI creates `.gemini`.

## Bundles (plugins)

| Client | Mechanism | What a bundle can carry |
|---|---|---|
| Claude Code | User-scope plugin, installed from a marketplace (a folder or git repo with `.claude-plugin/marketplace.json`) | Agents, skills, hooks, scripts. Scripts are referenced through `${CLAUDE_PLUGIN_ROOT}`, which changes on update, so no state may be stored there. |
| Codex CLI | `~/.agents/plugins/marketplace.json` plus `~/.codex/plugins/<plugin>/` | Skills, MCP servers, hooks. Agents are not a documented plugin component. |
| Kiro | None documented beyond the plain folders above. MCP servers merge into `~/.kiro/settings/mcp.json`. | Agents, steering, skills, hooks as plain files. |
| Gemini CLI | Extension folder under `~/.gemini/extensions/<name>/` with `gemini-extension.json`, installed with `gemini extensions install <path or GitHub URL>` | Agents, skills, commands, hooks, GEMINI.md, MCP servers. Extension agents and skills rank below user-level ones. |
| Copilot CLI and VS Code | `~/.copilot/installed-plugins/`, Agent Plugins 1.0 format | Agents, skills, MCP, hooks. VS Code finds CLI-installed plugins only when `chat.plugins.enabled` is on, default off. |

## Where the current pack disagrees with this file

1. Hooks are merged into each repository's `.claude/settings.json`. User-level hooks belong in the files listed above.
2. The hook command uses `${CLAUDE_PROJECT_DIR}/hooks/...`, which points at the repository, not the pack. A user-level install needs an absolute path to the pack or a plugin root.
3. The controller and hook script are copied into every repository. They can live once in the user profile.
4. Instructions are appended to each repository's AGENTS.md. User-level instruction files exist for all three clients.
5. Copilot skills are installed only to `~/.agents/skills`, which the CLI ignores when `COPILOT_HOME` is set. `~/.copilot/skills` is the reliable location.
6. Codex and Copilot hooks ship as repository samples. Both clients now have user-level hook locations.

## Still to verify by hand

- Whether user-level Claude Code hooks receive `CLAUDE_PROJECT_DIR`, and whether `~` expands in a hook command.
- Whether VS Code Copilot-harness sessions read `~/.copilot/agents` with default settings.
- Which shell runs Codex hook commands on native Windows.
- Whether Codex CLI loads plugin hooks; the docs disagree.

## Sources

- Claude Code: code.claude.com/docs/en/sub-agents, /skills, /hooks, /memory, /settings, /claude-directory, /plugins/install, /plugins/manifest-reference, /changelog
- Codex CLI: learn.chatgpt.com/docs/agent-configuration/subagents, /agent-configuration/agents-md, /build-skills, /hooks, /config-file/environment-variables, /windows/windows-app; developers.openai.com/plugins/build/plugins; github.com/openai/codex releases
- GitHub Copilot CLI: docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference, /cli-config-dir-reference, /cli-plugin-reference, /reference/hooks-reference, /how-tos/copilot-cli/customize-copilot/add-custom-instructions; github.com/github/copilot-cli changelog
- Kiro: kiro.dev/docs/custom-agents, /steering, /skills, /hooks, /mcp/configuration, /configuration, kiro.dev/changelog
- Gemini CLI: geminicli.com/docs/core/subagents, /cli/skills, /cli/gemini-md, /extensions/reference, /hooks, /reference/configuration, /changelogs/latest
- VS Code: code.visualstudio.com/docs/agent-customization/custom-agents, /agent-skills, /custom-instructions, /hooks, /agent-plugins; code.visualstudio.com/docs/agents/reference/ai-settings
