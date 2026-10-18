# Client locations

Verified 2026-10-18 against each vendor's official documentation. Every client was re-verified the same day after the first pass, and the versions installed on the reference machine were read from the programs themselves.

This file records where each targeted AI client reads configuration that applies in every repository (**user level**), and the repository folders it reads (**workspace level**) where the orchestration templates need them. The setup script and the orchestration templates must follow it. Vendors moved several of these paths during 2026, so re-verify before changing either, and update the date above. A weekly workflow checks the facts in `client-facts.json` against the vendors' pages.

`~` means the user profile: `%USERPROFILE%` on Windows, `$HOME` on macOS and Linux.

## Surfaces and the folders they read

Several surfaces run the same engine and therefore read the same home folder.

| Surface | Engine it runs | User-level folder | Notes |
|---|---|---|---|
| Claude Code extension in VS Code | Its own bundled copy of Claude Code | `~/.claude` | Reads the same settings, agents, skills, MCP and plugin files as the CLI, but offers only a subset of its commands and skills. |
| Codex extension in VS Code (`openai.chatgpt`) | Its own bundled Codex | `~/.codex`, plus `~/.agents/skills` | Shares configuration with the CLI. Does not support plugins. |
| GitHub Copilot in VS Code | Built into VS Code. The **Copilot harness** (Copilot SDK) is being rolled out as the default; the older **Local harness** will be removed in a future release. | `~/.copilot`, plus `~/.agents/skills` and `~/.claude/skills` | The two harnesses read different folders; see the tables below. |
| VS Code's agent interface: Chat view and Agents window, **Claude harness** | Claude Agent SDK | `~/.claude` | Enabled by default (`github.copilot.chat.claudeAgent.enabled`). |
| VS Code's agent interface, **Codex harness** | The Codex extension, or the Agent Host integration | `AGENTS.md` and `.agents/skills`; whether it reads `~/.codex` is not documented | The Agent Host integration is experimental and off by default (`chat.agentHost.codexAgent.enabled`). Codex sessions from the extension run only in the main window, not the Agents window. |
| Claude Code CLI, Claude desktop app (Code tab) | Claude Code | `~/.claude` | The desktop app's Cowork tab uses claude.ai settings, not `~/.claude`. |
| Codex CLI, ChatGPT desktop app (Codex view) | Codex | `~/.codex`, plus `~/.agents/skills` | The standalone Codex app merged into the ChatGPT desktop app on 2026-07-09. |
| Copilot CLI, GitHub Copilot app | Copilot CLI; the app is built on it | `~/.copilot`, plus `~/.agents/skills` | The app has been generally available since 2026-06-17 on Windows, macOS and Linux. |
| Kiro IDE, Kiro CLI | One agent harness shared by both | `~/.kiro` | CLI V3 is opt-in (`kiro-cli --v3`) until CLI 3.0, due at the end of October 2026. |
| Google Antigravity IDE, App and CLI | Antigravity | `~/.gemini/config`, plus a data folder per surface: `~/.gemini/antigravity-ide`, `~/.gemini/antigravity`, `~/.gemini/antigravity-cli` | Legacy workflows stop working on 2026-10-19. |

**Model engines.** Kiro's default is **Auto**, Kiro's model router, which sends each request to frontier models from Anthropic and OpenAI or to open-weight models; the docs refer to Amazon Bedrock for how requests are routed. Amazon Nova is not among Kiro's documented models. Kiro users can pick a model in the chat, and a custom agent can set `model`. An Antigravity agent's `model` is a tier, `inherit`, `flash` or `pro`, not a model name.

## Versions checked

| Client | What the docs reflect | Installed on the reference machine |
|---|---|---|
| Claude Code | Changelog through 2.1.302 (2026-10-16) | CLI 2.1.302; VS Code extension 2.1.301 |
| OpenAI Codex | CLI rust-v0.163.0 (2026-10-15); ChatGPT desktop app's Codex 26.1007 (2026-10-08) | CLI 0.163.0; VS Code extension 26.1007.21434 |
| GitHub Copilot CLI | Changelog through 1.0.98 (2026-10-14) | Not on the path; the app's copy is used |
| GitHub Copilot app | Generally available since 2026-06-17 | 1.1.30 |
| VS Code with GitHub Copilot | VS Code 1.142 (2026-10-14), Copilot built in | 1.142.0 |
| Kiro | IDE 1.3.11 (2026-10-15), CLI 2.31.1 (2026-10-14) | IDE 1.3.11; CLI 2.32.0, newer than the changelog |
| Google Antigravity | IDE 2.5.5 (2026-08-13), App 2.24.0 (2026-10-15), CLI 1.4.0 (2026-10-16) | IDE 2.5.5, App 2.24.0; CLI not on the path |
| Gemini CLI | v0.64.0 (2026-10-13), not re-checked in the second pass. Unpaid and Google One users were moved to Antigravity CLI on 2026-06-18. | Not installed |

## Agents

| Client | User level | Workspace | Format | Notes |
|---|---|---|---|---|
| Claude Code: CLI, VS Code extension, desktop app, VS Code Claude harness | `~/.claude/agents/`, subfolders included | `.claude/agents/` in every folder from the working directory up to the repository root; the closest wins | Markdown with YAML frontmatter. `name` and `description` are required. | Order on a name clash: managed, `--agents` flag, project, user, plugin. A file missing either field, or with YAML that does not parse, is skipped silently. |
| Codex: CLI, VS Code extension, ChatGPT desktop app | `~/.codex/agents/*.toml` | `.codex/agents/*.toml` | TOML. `name`, `description` and `developer_instructions` are required. | Markdown agents are not read. An agent file cannot set `sandbox_mode`, `approval_policy`, `model_provider` or `mcp_servers`. |
| Copilot CLI | `~/.copilot/agents/`, as `.agent.md` or `.md` | `.github/agents/`, then `.claude/agents/`, each from the working directory up to the git root | Markdown with frontmatter. `description` is required. | Personal agents win a name clash. `~/.claude/agents` is not read. |
| GitHub Copilot app | Not stated on the app's own pages. GitHub's custom-agents page says agents in `~/.copilot/agents/` become available to the app. | `.github/agents/` | As Copilot CLI | Chosen with the agent picker or `/agent`. |
| VS Code, Copilot harness | `~/.copilot/agents` | `.github/agents` | `.agent.md` | Read only when `github.copilot.chat.cli.customAgents.enabled` is on, and it defaults to off. |
| VS Code, Local harness | VS Code profile storage | `.github/agents` | `.agent.md` | The `chat.agentFilesLocations` setting applies to this harness only and is deprecated. |
| Kiro IDE and CLI | `~/.kiro/agents/<name>.md` or `.json` | `.kiro/agents/`, loaded only in a trusted workspace | Markdown with frontmatter, the body being the prompt, or JSON. No field is required; `name` defaults to the file name. | The workspace agent wins a name clash. CLI V2 reads JSON only. The IDE ignores an agent's `hooks` field. |
| Antigravity App and CLI | `~/.gemini/config/agents/<name>.md` or `<name>/agent.md` | `.agents/agents/` | Markdown with frontmatter. `name` and `description` are required. | Optional: `tools`, `mainAgent` and `subagent` (both default true), `model`, `commandExecutionPolicy`, `mcpServers`, `skills`, `plugins`. Subagents nest up to 10 deep. |
| Antigravity IDE | Not documented | Not documented | | Google's announcement of custom agents (2026-08-12) said the IDE would follow "shortly". |
| Gemini CLI | `~/.gemini/agents/*.md` | | Markdown. `name` and `description` are required. | Experimental. Invoked with `@name`. |

## Skills

| Client | User level | Workspace | Notes |
|---|---|---|---|
| Claude Code | `~/.claude/skills/<name>/SKILL.md` | `.claude/skills/` from the working directory up to the repository root | Every frontmatter field is optional; `name` defaults to the folder name. The folder names `synced` and `anthropic-skills` are reserved. Personal skills win over project skills. |
| Codex | `~/.agents/skills/<name>/SKILL.md` | `.agents/skills/` from the working directory up to the repository root | `name` and `description` are required. `~/.codex/skills` is deprecated but still loaded. The user path follows `$HOME`, not `CODEX_HOME`. |
| Copilot CLI and the Copilot app | `~/.copilot/skills/` and `~/.agents/skills/` | `.github/skills/`, `.agents/skills/`, `.claude/skills/` | `~/.claude/skills` is not read. `~/.agents/skills` stops being read when `COPILOT_HOME` or `--config-dir` is set. Name up to 64 characters, description up to 1024. |
| VS Code | `~/.copilot/skills/`, `~/.claude/skills/`, `~/.agents/skills/` | `.github/skills/`, `.claude/skills/`, `.agents/skills/` | The name uses lowercase letters, digits and hyphens and equals the folder name. The docs do not say which harness reads `~/.claude/skills`. |
| Kiro IDE and CLI | `~/.kiro/skills/<name>/SKILL.md` | `.kiro/skills/` | `name`, equal to the folder name, and `description` are required. No other tool's skill folder is read. |
| Antigravity App and IDE | `~/.gemini/config/skills/<name>/`; the IDE also reads the legacy `~/.gemini/antigravity/skills/` | `.agents/skills/`, legacy `.agent/skills/` | `description` is required, `name` is optional. `~/.agents/skills` is not documented. |
| Antigravity CLI | `~/.gemini/antigravity-cli/skills/<name>/` | `.agents/skills/` | Other Antigravity pages give `~/.gemini/config/skills/` without naming a surface. |
| Gemini CLI | `~/.gemini/skills/<name>/SKILL.md` or `~/.agents/skills/` | | The `.agents/skills` alias takes precedence over `.gemini/skills`. |

**Reach of the shared folder.** `~/.agents/skills` serves Codex, Copilot CLI, the Copilot app and VS Code. Claude Code, Kiro and Antigravity do not read it, so a skill meant for every client must also be installed into `~/.claude/skills`, `~/.kiro/skills` and `~/.gemini/config/skills`.

## Instructions that apply to every repository

| Client | User level | Workspace | Notes |
|---|---|---|---|
| Claude Code | `~/.claude/CLAUDE.md` and `~/.claude/rules/*.md` | `CLAUDE.md`, `.claude/CLAUDE.md`, `.claude/rules/`, and `AGENTS.md` only when the project has no CLAUDE.md (2.1.277 and later) | `paths` is the only frontmatter field a rule may use. There is no user-level AGENTS.md. A separate rules file avoids editing the user's own CLAUDE.md. |
| Codex | `~/.codex/AGENTS.md` | `AGENTS.md` from the project root down to the working directory, one per folder | If `~/.codex/AGENTS.override.md` exists it replaces the base file, so the installer must never create it. Codex stops adding files at 32 KiB in total (`project_doc_max_bytes`). Projects that are not trusted supply no AGENTS.md (0.150.0). In the ChatGPT desktop app, Settings > Personalization edits the same personal file. |
| Copilot CLI | `~/.copilot/copilot-instructions.md` and `~/.copilot/instructions/**/*.instructions.md` | `.github/copilot-instructions.md`, `.github/instructions/`, `AGENTS.md`, `CLAUDE.md`, `.claude/CLAUDE.md`, `GEMINI.md`, `.claude/rules/` | Subagents skip AGENTS.md unless the agent sets `include-custom-instructions: true`. |
| GitHub Copilot app | "App instructions" in Settings > Sessions > Instructions; where they are stored is not documented | Settings > Projects, or `instructions:` in `.github/github-app.yml`, which the user must accept before it applies | Whether the app reads `~/.copilot/instructions` is not documented. |
| VS Code | Copilot harness: `~/.copilot/copilot-instructions.md` and `~/.copilot/instructions`. Claude harness: `~/.claude/CLAUDE.md` and `~/.claude/rules`. Local harness: profile storage. | `.github/copilot-instructions.md`, `AGENTS.md`, `.github/instructions/`; for Claude, `CLAUDE.md` and `.claude/rules`; for Codex, `AGENTS.md` | `chat.useAgentsMdFile` defaults to on. |
| Kiro IDE and CLI | `~/.kiro/steering/*.md`; an `AGENTS.md` there is always included | `.kiro/steering/` and `AGENTS.md` | Optional frontmatter `inclusion`: `always` (the default), `fileMatch` with `fileMatchPattern`, `manual`, or `auto` with `name` and `description`. CLI V1 and V2 load only `always` files automatically. |
| Antigravity, all surfaces | `~/.gemini/AGENTS.md`, `~/.gemini/GEMINI.md`, `~/.gemini/config/rules/*.md`; the CLI also reads `~/.gemini/antigravity-cli/rules/` | `AGENTS.md`, `GEMINI.md` and `.agents/rules/*.md` in the workspace or any subfolder, legacy `.agent/rules/` | A file in `rules/` needs frontmatter `trigger` set to `always_on`, `model_decision` (with `description`), `glob` (with `globs`) or `manual`; a missing or invalid trigger drops the file silently. Up to 24,000 bytes per file, and 20,000 tokens across all active global and always-on rules. |
| Gemini CLI | `~/.gemini/GEMINI.md` | | Plain Markdown with `@file.md` imports. |

## Hooks

| Client | User level | Workspace | Notes |
|---|---|---|---|
| Claude Code | `hooks` key in `~/.claude/settings.json` | `.claude/settings.json`, `.claude/settings.local.json` | There is no standalone hooks file. On Windows a command runs in Git Bash when it is installed, otherwise in PowerShell; `"shell": "powershell"` forces PowerShell. `${CLAUDE_PROJECT_DIR}` is the repository being worked on, so it cannot point at the pack. |
| Codex | `~/.codex/hooks.json`, or `[hooks]` in `~/.codex/config.toml` | `.codex/hooks.json` or `.codex/config.toml`, in trusted projects | A layer that holds both is merged with a warning, so use one. Each hook runs only after the user trusts it with `/hooks`, and again after any edit. `commandWindows` sets a Windows command. How to trust hooks in the VS Code extension or the app is not documented. |
| Copilot CLI | `~/.copilot/hooks/*.json`, or `hooks` in `~/.copilot/settings.json` | `.github/hooks/*.json`, `.github/copilot/settings.json`, `.claude/settings.json` | `config.json` is no longer read for hooks. |
| GitHub Copilot app | Not documented | | GitHub's hooks reference names only Copilot CLI and the cloud agent; the app's plugins can carry hooks. |
| VS Code | Copilot harness: the same hooks as Copilot CLI. Local harness: `~/.copilot/hooks/*.json`, and Claude's settings files only when `chat.useClaudeHooks` is on. Claude harness: Claude Agent SDK hooks. | `.github/hooks/` | VS Code's hooks experience is a preview. |
| Kiro | `~/.kiro/hooks/*.json`, documented for CLI V3 only | `.kiro/hooks/*.json`, IDE 1.0 and CLI V3 | JSON with `version: "v1"` and a `hooks` list of `name`, `trigger`, optional `matcher`, and `action` (`command` or `agent`). Exit code 2 blocks the event. CLI V2 keeps hooks inside the agent file instead. |
| Antigravity, all surfaces | `~/.gemini/config/hooks.json`; the CLI also accepts hooks inside `~/.gemini/antigravity-cli/settings.json` | `.agents/hooks.json` | Events: SessionStart, PreToolUse, PostToolUse, PreInvocation, PostInvocation, Stop. Each handler needs `command`; the default timeout is 30 seconds; input and output are JSON. |
| Gemini CLI | `hooks` key in `~/.gemini/settings.json` | | Events: SessionStart, SessionEnd, BeforeAgent, AfterAgent, BeforeModel, AfterModel, BeforeToolSelection, BeforeTool, AfterTool, PreCompress, Notification. |

## Slash commands and workflows

A skill is the one form that every client runs as a slash command. The older forms are deprecated or limited:

- **Claude Code:** `~/.claude/commands/*.md` still works, but commands were merged into skills, and a skill of the same name wins.
- **Codex:** custom prompts in `~/.codex/prompts/` are deprecated in favour of skills.
- **Copilot CLI:** no prompt files; each skill runs as `/name`, and a repository's `.claude/commands/` is read.
- **VS Code:** `.prompt.md` files run only in the Local harness; the Copilot harness uses skills.
- **Kiro:** each skill runs as `/name`, and so does a `manual` steering file. Saved workflows (JSON or YAML recipes) live in `~/.kiro/workflows/` and `.kiro/workflows/`.
- **Antigravity:** workflows in `~/.gemini/config/workflows/` and `.agents/workflows/` stop working on 2026-10-19; `/migrate-workflows` in the App converts them to skills. A replacement workflows system is announced but not documented.

## Delegation to subagents

How a main agent hands work to another agent in each client. The orchestration templates build on this.

- **Claude Code:** the `Agent` tool runs any agent from the agent folders.
- **Codex:** the TOML agents are its subagents; `[agents]` in `config.toml` sets limits such as `max_concurrent_threads_per_session`.
- **Copilot CLI and the app:** the `agent` tool.
- **VS Code:** in the Local harness, the `agent` tool (`runSubagent`) limited by an agent's `agents` list, plus `handoffs` buttons. The Copilot, Claude and Codex harnesses use their own subagents. Whether the Copilot harness honours `handoffs` is not documented.
- **Kiro:** the `subagent` tool.
- **Antigravity App and CLI:** `invoke_subagent` calls any agent that sets `subagent: true`.

## MCP servers

| Client | User level | Workspace |
|---|---|---|
| Claude Code | `mcpServers` in `~/.claude.json` | `.mcp.json` at the repository root |
| Codex | `[mcp_servers.<name>]` in `~/.codex/config.toml` | `.codex/config.toml`, in trusted projects |
| Copilot CLI and the app | `~/.copilot/mcp-config.json` | `.mcp.json` and `.github/mcp.json`, in trusted folders |
| VS Code, Copilot harness | `~/.copilot/mcp-config.json`, or the same file under `COPILOT_HOME` | `.mcp.json`; `.vscode/mcp.json` is not read directly |
| Kiro IDE and CLI | `~/.kiro/settings/mcp.json` | `.kiro/settings/mcp.json`, which wins on conflict |
| Antigravity IDE and CLI | `~/.gemini/config/mcp_config.json` | `.agents/mcp_config.json` |
| Antigravity App | Managed in Settings > Installed MCP Servers; no file is documented | |

## Relocating the configuration folder

- `CLAUDE_CONFIG_DIR` moves every `~/.claude` path, including `.claude.json`. The VS Code extension accepts only an absolute path, and project settings cannot set it.
- `CODEX_HOME` moves `~/.codex` (configuration, agents, hooks, the global AGENTS.md), but not `~/.agents/skills` or `~/.agents/plugins`. The folder must already exist. Codex inside WSL uses the Linux home unless `CODEX_HOME` points at the Windows one. Whether the ChatGPT desktop app honours it is not documented.
- `COPILOT_HOME` replaces `~/.copilot` and stops the CLI reading `~/.agents/skills`; `--config-dir` is deprecated. VS Code documents it for MCP only, and the Copilot app's pages do not mention it.
- `KIRO_HOME` moves the Kiro CLI's global folder (V3). IDE support is undocumented.
- Antigravity documents no relocation variable.
- `GEMINI_CLI_HOME` sets the folder in which Gemini CLI creates `.gemini`.

## Bundles (plugins)

| Client | Mechanism | What a bundle can carry |
|---|---|---|
| Claude Code | User-scope plugin from a marketplace (a folder or git repository with `.claude-plugin/marketplace.json`), installed under `~/.claude/plugins/` | Agents, skills, commands, hooks, MCP servers and more. Plugin agents ignore `hooks`, `mcpServers` and `permissionMode`. Scripts are referenced through `${CLAUDE_PLUGIN_ROOT}`, which changes on update, so no state may be stored there. |
| Codex | `~/.agents/plugins/marketplace.json`; installed copies in `~/.codex/plugins/cache/` | Skills, MCP servers, hooks. The VS Code extension does not support plugins. |
| Copilot CLI, the app and VS Code | `~/.copilot/installed-plugins/`, Agent Plugins 1.0 format; the app's Customize > Plugins | Agents, skills, MCP servers, hooks; the app adds canvas extensions. VS Code finds them only when `chat.plugins.enabled` is on, and it defaults to off. |
| Kiro | Powers in `~/.kiro/powers/`, Agent Plugins format with `plugin.json` | Skills and MCP servers. A custom agent opts in with `includePowers`. |
| Antigravity | `~/.gemini/config/plugins/<name>/` with `plugin.json`; the CLI also stages plugins in `~/.gemini/antigravity-cli/plugins/` | MCP configuration, hooks, skills, agents, rules. |
| Gemini CLI | Extension folder under `~/.gemini/extensions/<name>/` with `gemini-extension.json` | Agents, skills, commands, hooks, GEMINI.md, MCP servers. |

## Agent file fields and tool identifiers

Verified 2026-10-18. A pack validator should reject anything not listed here.

| Client | Required fields | `tools` syntax and valid values | Other documented fields |
|---|---|---|---|
| Claude Code | `name` (up to 256 characters, no colon, not starting with a hyphen) and `description`; a file without both is skipped | Comma-separated string or YAML list. Built-ins: Read, Grep, Glob, LSP, Bash, PowerShell, Edit, Write, NotebookEdit, WebFetch, WebSearch, TodoWrite, Skill, ToolSearch, Agent, EnterWorktree, ExitWorktree, Monitor, TaskStop, SendMessage, Artifact. MCP: `mcp__<server>__*`. If no entry resolves, the agent fails to launch. Use the `skills` field to preload skills, not `tools: Skill`. | `disallowedTools`, `model` (sonnet, opus, haiku, fable, full ID, inherit), `permissionMode`, `maxTurns`, `autoCompactWindow`, `skills`, `mcpServers`, `hooks`, `memory` (user, project, local), `background`, `omitClaudeMd`, `effort`, `isolation: worktree`, `color`, `initialPrompt` |
| Copilot CLI and VS Code | `description` (VS Code treats the header as optional) | String array or comma-separated string. Aliases, case-insensitive: execute, read, edit, search, agent, web, todo. `*` grants everything, `[]` disables all, `server/tool` and `server/*` for MCP. Unrecognised names are ignored silently. | `name`, `include-custom-instructions` (default false), `model`, `models`, `modelPolicy`, `reasoningEffort`, `mcp-servers`, `hooks`. `infer` is retired. VS Code adds `user-invocable`, `disable-model-invocation`, `handoffs`, `agents`, `argument-hint`, `target`. |
| Codex | `name`, `description`, `developer_instructions` | No tools field. | `model`, `model_reasoning_effort`, `model_reasoning_summary`, `model_verbosity`, `features.*`, `skills.config`. Ignored if set: `sandbox_mode`, `approval_policy`, `model_provider`, `mcp_servers`. |
| Kiro | None; `name` defaults to the file name | List of tool names; APM requires each to be one of read, write, shell, web, subagent, knowledge, context, todo_list, @mcp, @builtin, or `*`. | `description`, `prompt`, `model`, `excludedTools`, `includeMcpJson`, `includePowers`, `resources` (`file://`, `skill://`), `permissions`, `mcpServers`, `welcomeMessage`; CLI V3 adds `hooks` |
| Antigravity App and CLI | `name`, `description` | A `tools` list; the valid names are not yet verified. | `mainAgent`, `subagent`, `model` (inherit, flash, pro), `commandExecutionPolicy` (off, auto, eager, sandbox; default sandbox), `mcpServers`, `skills`, `plugins` |
| Gemini CLI | `name` (lowercase letters, digits, hyphens, underscores), `description` | YAML list. Built-ins: run_shell_command, glob, grep_search, list_directory, read_file, read_many_files, replace, write_file. Wildcards `*`, `mcp_*`, `mcp_<server>_*`. Omitted means inherit all. | `kind` (local, remote), `max_turns` (default 30), `model`, `temperature`, `timeout_mins`, `mcpServers` |

## APM (Agent Package Manager, Microsoft)

Verified 2026-10-18 against microsoft.github.io/apm and the installed CLI 0.33.0.

- **Manifest.** `apm.yml` requires only `name` and `version`. Optional: `description`, `author`, `license` (SPDX), `homepage`, `repository`, `keywords`, `targets` (list of copilot, claude, codex, gemini, kiro, cursor, opencode, windsurf, antigravity, agent-skills, grok-build, hermes; `vscode` is a deprecated alias for copilot), `scripts`, `includes`, `dependencies` (`apm`, `mcp`, `lsp`), `devDependencies`, `compilation`, `policy`, `registries`, `marketplace`. There is no top-level `source`, `agents`, or `skills` field; those names exist only inside `marketplace.packages[]` and per-dependency objects. Unknown fields are not an error, but they do nothing.
- **Layout.** `.apm/` is the source root. Primitives: `.apm/instructions/*.instructions.md` (frontmatter `description`, `applyTo`), `.apm/prompts/*.prompt.md`, `.apm/agents/*.agent.md` (frontmatter `name`, `description`, optional `model`, `tools`, `color`, `handoffs`), `.apm/skills/<name>/SKILL.md` (`name` equals the folder), `.apm/hooks/*.json`, and MCP servers declared in `apm.yml`. Commands ship as prompts.
- **Deployment per target (project scope).** Agents go to `.github/agents/*.agent.md`, `.claude/agents/*.md`, `.codex/agents/*.toml`, `.kiro/agents/*.md`; Gemini gets no agents. Skills go to `.agents/skills/` for Copilot, Codex, Gemini, and agent-skills, `.claude/skills/` for Claude, `.kiro/skills/` for Kiro. Instructions become `.github/instructions/`, `.claude/rules/`, `.kiro/steering/`, and are folded into `AGENTS.md` for Codex and `GEMINI.md` for Gemini. Hooks go to `.github/hooks/`, merged `.claude/settings.json`, `.codex/hooks.json`, `.kiro/hooks/`, merged `.gemini/settings.json`.
- **User scope (`apm install -g`).** Full for Claude Code. Copilot: prompts and instructions only; agents and hooks stay project scope. Codex: agents, skills, hooks, MCP; no instructions or prompts. So a user-wide install of Copilot agents must be done by our installer, not APM.
- **One repo, many packs.** A dependency may point at a sub-folder: `apm install owner/repo/path/to/pack`, or the object form with `git`, `path`, `ref`.
- **Verbatim copying (observed with 0.33.0 on 2026-10-18).** Agent frontmatter is copied unchanged to Claude Code and Copilot; Codex keeps only name, description, and body; Kiro keeps description, model, tools and fails closed unless every tool is one of read, write, shell, web, subagent, knowledge, context, todo_list, @mcp, @builtin, *. There is no per-target override. Hook commands are copied unchanged and hook scripts are not deployed. Prompt frontmatter keys unsupported by Claude commands (such as `agent`) are dropped with a warning.
- **Antigravity target.** Listed by APM 0.33.0; what it generates there is not yet observed.
- **Validation.** `apm install` rejects malformed YAML and blocks on critical hidden-Unicode findings. `apm compile --validate` checks every primitive's frontmatter. `apm audit --ci` checks lockfile, deployed files, drift, orphaned packages, and content integrity. There is no `apm lint` and no `apm validate`.
- **"Official" packages.** APM has no approval or badge concept. Distribution is a `marketplace:` block in `apm.yml`, built with `apm pack`, registered by consumers with `apm marketplace add`. Organisations restrict allowed marketplaces by policy and trust packages with `apm approve`. `apm publish` to a registry is experimental.

## Client notes

**Google Antigravity**
- Settings: the App reads `~/.gemini/config/config.json`; the CLI reads `~/.gemini/antigravity-cli/settings.json`; the IDE documents only its settings screen.
- AGENTS.md is read on every surface. `~/.claude` and `~/.agents/skills` are not mentioned anywhere in the docs.
- The docs disagree on the CLI's global skills folder and plugin folder (both `~/.gemini/antigravity-cli/...` and `~/.gemini/config/...` appear), on whether an MCP server may use `url` instead of `serverUrl`, and on whether `plugin.json` requires `name`.

**Kiro**
- The docs disagree on whether custom agents load steering files and skills by default. The configuration reference says they inherit them unless `chat.disableInheritingDefaultResources` is true; the steering and skills pages say they do not.
- Permissions live in `~/.kiro/settings/permissions.yaml`, with per-workspace copies under `~/.kiro/workspace-roots/`, so a cloned repository cannot add permission rules. CLI settings live in `~/.kiro/settings/cli.json`.

**GitHub Copilot app**
- Built on Copilot CLI: skills and MCP servers configured for Copilot CLI or the repository are available automatically.
- Canvas extensions live in `~/.copilot/extensions` and `.github/extensions`.

## GitHub Copilot code review (on GitHub.com)

Verified 2026-10-18 against docs.github.com.

- Reads, from the pull request's head branch: `.github/copilot-instructions.md`, path-specific `.github/instructions/**/*.instructions.md` (frontmatter `applyTo`; `excludeAgent: "code-review"` opts a file out), agent instruction files `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `REVIEW.md`, agent skills in `.github/skills`, and organisation-level instructions.
- Custom agents in `.github/agents` do not influence code review. No user-profile file applies; personal instructions apply only to Copilot CLI.
- Keep any single instruction file under about 1,000 lines. Priority: personal, then repository, then organisation.

## Where the current pack disagrees with this file

1. Hooks are merged into each repository's `.claude/settings.json`. User-level hooks belong in the files listed above.
2. The hook command uses `${CLAUDE_PROJECT_DIR}/hooks/...`, which points at the repository, not the pack. A user-level install needs an absolute path to the pack or a plugin root.
3. The controller and hook script are copied into every repository. They can live once in the user profile.
4. Instructions are appended to each repository's AGENTS.md. User-level instruction files exist for all three clients.
5. Copilot skills are installed only to `~/.agents/skills`, which the CLI ignores when `COPILOT_HOME` is set. `~/.copilot/skills` is the reliable location.
6. Codex and Copilot hooks ship as repository samples. Both clients now have user-level hook locations.

## Still to verify by hand

- Whether the Antigravity IDE reads custom agents from `~/.gemini/config/agents/`, which is announced but not documented.
- Which global skills folder the Antigravity CLI reads.
- Whether the GitHub Copilot app reads `~/.copilot/agents`, `~/.copilot/instructions` and `~/.copilot/hooks`.
- In VS Code's Copilot harness: whether custom agents appear once `github.copilot.chat.cli.customAgents.enabled` is on, and whether `handoffs` work.
- Which VS Code harness reads `~/.claude/skills`, and whether a skill installed in both `~/.claude/skills` and `~/.agents/skills` appears twice.
- Whether the Kiro IDE runs global hooks from `~/.kiro/hooks/`, and whether Kiro custom agents load steering files and skills by default.
- Whether the ChatGPT desktop app honours `CODEX_HOME`, and how Codex hooks are trusted outside the CLI.
- Whether user-level Claude Code hooks receive `CLAUDE_PROJECT_DIR`, and whether `~` expands in a hook command.
- Which shell runs Codex hook commands on native Windows.

## Sources

- Claude Code: code.claude.com/docs/en/sub-agents, /skills, /memory, /hooks, /settings, /mcp, /mcp-quickstart, /env-vars, /claude-directory, /debug-your-config, /vs-code, /desktop, /plugins/components, /plugins/install, /plugins/loading, /plugins/manifest-reference, /changelog
- Codex: learn.chatgpt.com/docs/agent-configuration/subagents, /agent-configuration/agents-md, /build-skills, /hooks, /custom-prompts, /extend/mcp, /plugins, /config-file/environment-variables, /windows/windows-app, /whats-new, /changelog; developers.openai.com/plugins/build/plugins; github.com/openai/codex releases and source
- GitHub Copilot CLI and app: docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference, /cli-config-dir-reference, /cli-plugin-reference, /reference/hooks-reference, /reference/custom-agents-configuration, /reference/github-copilot-app-reference, /how-tos/copilot-cli/customize-copilot/add-custom-instructions, /how-tos/github-copilot-app/customize-github-copilot-app, /concepts/agents/cloud-agent/about-custom-agents; github.blog/changelog/2026-06-17-github-copilot-app-generally-available; github.com/github/copilot-cli changelog
- VS Code: code.visualstudio.com/docs/agent-customization/custom-agents, /agent-skills, /custom-instructions, /prompt-files, /hooks, /mcp-servers, /agent-plugins, /migrate-customizations; /docs/agents/run/agent-harnesses, /agents-window, /subagents; /docs/agents/reference/ai-settings
- Kiro: kiro.dev/docs/custom-agents, /custom-agents/configuration-reference, /steering, /skills, /hooks, /specs, /mcp/configuration, /powers, /permissions, /configuration, /reference/settings, /models, /models/available-models, /cli/v3; kiro.dev/changelog
- Google Antigravity: antigravity.google/docs/rules, /skills, /subagents, /hooks, /mcp, /plugins, /settings, /ide/workflows, /migration/workflows-to-skills, /cli/commands/agents, /changelog
- Gemini CLI: geminicli.com/docs/core/subagents, /cli/skills, /cli/gemini-md, /extensions/reference, /hooks, /reference/configuration, /changelogs/latest
- APM: microsoft.github.io/apm reference pages manifest-schema, targets-matrix, package-anatomy, cli/install, cli/compile, cli/pack, cli/audit
- Copilot code review: docs.github.com/en/copilot/reference/custom-instructions-support, /how-tos/use-copilot-agents/use-code-review, /tutorials/customize-code-review
