# MASTER PROMPT — CREATE AN AGENT PACK FROM A ROLE

Prompt version 2.1 (2026-10-18). Vendor facts this prompt relies on are in `client-locations.md` in the same folder; read it before generating.

ROLE: [Enter the role here]

Create the complete Agent/Skill Pack for this role using the approved framework established in this conversation.

Reuse the framework, artifact structure, naming conventions, documentation depth, packaging, and validation standard. Author all role-specific content from scratch.

## 1. Derive the role requirements

Use the role, current conversation, and supplied reference files to establish:

- Mission, users, outcomes, scope, and non-goals
- Primary workflows and specialist capabilities
- Inputs, outputs, knowledge sources, and integrations
- Tools, permissions, dependencies, and operational constraints
- Security, privacy, responsible AI, failure handling, and escalation
- Examples, tests, acceptance criteria, and completion evidence

Fill meaningful capability gaps using current official documentation. Avoid peripheral Skills that do not materially support the role.

Do not ask me to repeat established information. Make reasonable assumptions and document them. Ask only when an unresolved decision would materially change the role or scope.

## 2. Preserve the canonical framework

The pack is an APM package. The canonical source is the `.apm/` folder, and every vendor file is generated from it. Include:

- `apm.yml` using only fields APM defines: `name`, `version`, `description`, `author`, `license` (SPDX), `repository`, `keywords`, and `targets` listing `copilot`, `claude`, `codex`, `gemini`, `kiro`, `agent-skills`. Do not add `source`, `agents`, or `skills` at the top level; APM ignores them.
- `.apm/agents/*.agent.md` (canonical agents)
- `.apm/skills/<name>/SKILL.md` (canonical Skills; folder name equals `name`)
- `.apm/instructions/*.instructions.md` with `description` and `applyTo` frontmatter
- `.apm/prompts/*.prompt.md` (the `agent` field is honoured by Copilot and dropped by Claude, which supports only description, input, allowed-tools, model, argument-hint)
- DESCRIPTION.md
- README.md
- AGENT-PACK-README.md: the artifact catalog. List every file with its purpose. Do not embed file contents.
- PORTABLE_AGENT_SKILL_PACK_AUTHORING_PROMPT.md: this prompt, with its version number
- LICENSE
- Uppercase VALIDATION_REPORT.md
- docs/
- compatibility/
- examples/
- templates/
- hooks/ for helper scripts and reviewed samples only. Do not ship native hook definitions: APM copies hook commands verbatim and never deploys the scripts they call, so any command path would break after install. Hook wiring belongs to the installer.
- tests/
- tooling/, including a build script that produces the distribution archives

Do not hand-build `targets/<vendor>/` trees. Vendor files are derived from `.apm/` by APM or by the Code Workflow installer at install time. Instead, prove generation works in validation (section 8).

Distribution archives and SHA256 checksums are build outputs produced by the tooling. Deliver them, but do not treat them as source.

Retain canonical artifact categories. If one is genuinely inapplicable, explain why rather than silently omitting it.

Preserve the framework's organizational pattern, but choose the number of Skills, specialists, prompts, examples, and templates according to the new role. Do not inherit another role's counts.

Leave nothing stale: no `__pycache__`, no duplicate vendor folders, no archives from earlier builds.

## 3. Design one primary technology or role agent

Create one user-facing primary agent that can handle the role's complete workflow.

Add optional specialist subagents only where separate expertise, context, permissions, or independent review provides concrete value. Do not create specialists merely to reproduce an organization chart.

Keep agent profiles thin. Place detailed procedures in focused Skills and shared contracts.

Primary and specialist profiles use each vendor's documented agent directory. Do not invent a separate subagents folder.

Define specialist activation, assignment boundaries, handoff inputs, required evidence, and return format. The primary remains responsible for integration and completion.

## 4. Operationalize every Skill and hook

For each Skill or hook, define:

1. Purpose and activation conditions
2. Scope and exclusions
3. Required inputs
4. Dependencies and available tools
5. Expected workflow or behavior
6. Expected output
7. Validation requirements
8. Failure handling and escalation
9. Permissions and guardrails
10. Connection to agent instructions and workflows

Keep individual Skills useful when installed separately. Make pack-level prompts and specialists optional unless a real dependency requires them.

Hooks must perform useful, bounded checks. Clearly distinguish native vendor hooks from portable scripts or manual helpers.

## 5. Install at user scope; use accurate tools and permissions

The pack must work when installed once into the user profile and used from every repository, in Claude Code, OpenAI Codex, GitHub Copilot (Copilot CLI and the VS Code agent pane), Kiro, and Gemini CLI. Therefore:

- Nothing may depend on files at a repository root. No `shared/` folders, and no repo-level `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, or `copilot-instructions.md` as a prerequisite. Repository-level instructions are an optional extra for GitHub Copilot code review, generated from `.apm/instructions`.
- Hook commands reference scripts by a path the installer supplies, never a repository-relative path such as `.github/hooks/scripts/...`.
- Instructions that must apply everywhere go in `.apm/instructions/` so they generate into `~/.claude/rules`, `~/.copilot/instructions`, `~/.kiro/steering`, and the Codex and Gemini context files.

Verify current official vendor Agent/Skill specifications before generating. Use the field names and tool identifiers recorded in `client-locations.md`:

- Do not set `tools` on canonical agents. APM copies the field verbatim to Claude Code and Copilot, drops it for Codex, and refuses the agent for Kiro unless every value is a Kiro tag, so no one value is valid everywhere. Declare each agent's intended permissions in `compatibility/tool-permissions.yml` (intents: read, edit, shell, web, delegate); the Code Workflow installer translates them per vendor.
- Claude Code: `name` and `description` are required. Preload Skills with the `skills` field.
- Copilot: `description` is required. `tools` uses the documented aliases (execute, read, edit, search, agent, web, todo) or specific tool names; unknown names are ignored silently, so never rely on them. Set `include-custom-instructions: true` when a subagent must read repository instructions.
- Codex: `name`, `description`, and `developer_instructions` are required. There is no tools field. Do not set `sandbox_mode`, `approval_policy`, `model_provider`, or `mcp_servers` in an agent file.
- Kiro: agents are Markdown with frontmatter; steering files carry an `inclusion` mode; hooks use the `v1` JSON schema.
- Gemini CLI: `name` must be a lowercase slug; `tools` uses Gemini tool names such as `read_file`, `grep_search`, `write_file`, `replace`, `run_shell_command`.
- Skills: `name` equals the folder name; `description` is at most 1024 characters.

Do not invent tool aliases, imply unavailable integrations, or claim that written instructions enforce security. If an agent forbids writing files, do not also give it a shell that can write them, or state the contradiction openly.

Apply least privilege and preserve existing user authorization within its scope. Require missing authority for consequential actions without repeatedly asking for approval already granted.

Do not install, publish, deploy, communicate externally, or change shared systems unless authorized.

## 6. Prevent content leakage

Previous packs are structural references only.

Do not carry forward unrelated personas, terminology, Skills, hooks, examples, business rules, integrations, or assumptions.

An element may recur only when independently relevant to the new role.

Create fresh canonical source rather than copying an entire previous pack and renaming it.

## 7. Produce the established downloads

Four primary downloads:

1. Full pack
2. Canonical Agent/Skill source (`apm.yml` plus `.apm/`)
3. Reusable authoring prompt
4. Validation bundle

Secondary downloads, each produced by the build script from `.apm/`:

- GitHub Copilot package
- Claude Code package
- OpenAI Codex package
- Kiro package
- Gemini CLI package
- Individual validated skill.zip archives
- Bundle of individual Skill archives
- SHA256 checksums

Make the canonical source installable with `apm install <owner>/<repo>/<pack-folder>` from a repository that holds several packs. State plainly which APM behaviours were exercised and which were not.

## 8. Validate the integrated pack

Verify:

- Required artifacts and sections exist
- `apm.yml` parses and uses only defined fields
- `apm compile --validate` passes, and `apm install --dry-run` for every declared target reports what it would deploy
- Content is specific to the requested role
- Skills, prompts, agents, hooks, and contracts reference existing files
- Vendor packages produced by the build contain their required dependencies
- Tool permissions match responsibilities, and no agent contradicts itself
- Metadata conforms to current vendor specifications in `client-locations.md`
- Examples demonstrate documented workflows
- Tests cover critical behavior and failure conditions
- Scripts and hooks execute correctly within their supported environment
- A user-scope install into a sandbox profile succeeds for every target, using `CLAUDE_CONFIG_DIR`, `CODEX_HOME`, `COPILOT_HOME`, `KIRO_HOME`, and `GEMINI_CLI_HOME`
- No irrelevant prior-role content, stale files, or unfinished placeholders remain
- Build outputs and archives match canonical source
- Archives are safe, complete, reproducible, and include the final validation report
- Individual Skill archives are valid
- Checksums match delivered archives

Correct discovered issues before delivery.

Distinguish structural checks, executable local tests, model behavior evaluations, and live integration evidence. Never describe an unexecuted check as passed. Appearance in the VS Code agent pane is live integration evidence and must be reported as not established unless actually observed.

## 9. Present the result

Save the complete pack in the current workspace.

Provide an ordered artifact catalog containing:

ARTIFACT NAME: PURPOSE: LOCATION:

List files; do not reproduce their contents.

Finish with a concise delivery response linking the four primary downloads, vendor packages, artifact catalog, and uppercase validation report.

End with AGENT PACK VALIDATION SUMMARY covering:

- Role implemented
- Artifacts represented
- Skills and optional specialists
- Hooks and triggers
- Knowledge sources and integrations
- Permissions and guardrails
- Tests actually executed
- Genuine gaps, assumptions, and unverified behavior

SAME FRAMEWORK. SAME COMPLETENESS STANDARD. FRESH ROLE-SPECIFIC CONTENT.

---

## Change log

### Version 2.1 (2026-10-18)

Proven by restructuring the Python Distinguished Engineer pack and installing it with APM 0.33.0 into a scratch project for all six targets.

- Section 2: no native hook definitions in a pack (APM deploys commands verbatim without their scripts); prompt `agent` field behaviour noted.
- Section 5: canonical agents carry no `tools`; permissions declared in `compatibility/tool-permissions.yml`.

### Version 2 (2026-10-18)

Driven by the review of the Python Distinguished Engineer pack 2.0.0 (`pack-review-python-distinguished-engineer.md`) and by vendor documentation verified the same day (`client-locations.md`).

- Section 2: `apm.yml` limited to fields APM defines; `instructions`, `prompts`, and native `hooks` moved under `.apm/`; hand-built `targets/<vendor>/` trees removed in favour of generation at install time; archives declared build outputs; catalog no longer embeds file contents; no stale files.
- Section 5: user-scope installation made a hard requirement; repository-root dependencies forbidden; verified field names and tool identifiers per vendor; Kiro added; self-contradicting permissions called out.
- Section 7: Kiro package added; monorepo install syntax stated.
- Section 8: APM validation commands and a sandbox user-scope install added; VS Code agent-pane appearance classed as live evidence.
- Section 9: catalog lists locations instead of contents.

### Version 1

The original prompt, as used to build the Microsoft Certified Trainer and Python Distinguished Engineer packs.
