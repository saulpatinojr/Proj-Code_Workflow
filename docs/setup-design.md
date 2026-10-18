# Setup: design decisions and status

Agreed 2026-10-18 and updated as work lands; last updated 2026-10-18. `client-locations.md` holds the verified folder locations this plan depends on, and `agent-pack-prompt.md` defines what a pack is.

## Goal

Install agent packs once, into the user profile, so every repository can use them in the clients the user works in, on Windows and macOS:

- VS Code, with the Claude Code, Codex and GitHub Copilot agents, including VS Code's own agent interface;
- Kiro, the IDE;
- Google Antigravity, both the IDE and the app;
- the GitHub Copilot app.

Work order: VS Code first (Claude Code, Codex, Copilot), then Kiro and Antigravity in either order. The apps must work as well as the IDEs: the Antigravity app, the GitHub Copilot app, and VS Code's agent interface.

Code Workflow is the light sibling of Code Conductor; the same packs serve both and must eventually be approved, official APM packages.

## How success is measured

- **Current threshold:** scripts pull the selected agent packs from GitHub into the installed clients' folder locations, and the orchestration for those clients is generated locally.
- **100%:** APM pulls the selected agent packs, and a minimal engine, perhaps a workflow, generates the customized orchestration for the clients installed on that desktop.

## Decisions

| Topic | Decision |
|---|---|
| What a pack is | The canonical layout of `agent-pack-prompt.md` (version 2.3): `apm.yml` and `.apm/` with agents, skills, instructions and prompts, plus docs, tests, hook samples and tooling. APM generates every client's files at install time; there are no hand-built vendor targets, and build archives are never committed. One pack per role, with one primary agent and optional specialists. |
| Source of truth | The public GitHub repository `saulpatinojr/Proj-Agent_Packs`. Every change arrives as a pull request; merging it is the approval. |
| Orchestrators | Not packs. An orchestrator is a client's main coordinating agent. It is generated for each desktop from the tools found there and the packs, agents and skills the user selected, using a template per client. The Codex seed is kept unchanged in `Proj-Agent_Packs/orchestrators/` as reference. Orchestration templates are the current priority; the next section holds their decisions. |
| Clients and their folders | Each engine reads its own home folder, shared by all its surfaces: `~/.claude` (Claude Code CLI, its VS Code extension, VS Code's Claude harness), `~/.codex` with `~/.agents/skills` (Codex CLI, its VS Code extension, the ChatGPT desktop app), `~/.copilot` (Copilot in VS Code, Copilot CLI, the Copilot app), `~/.kiro` (Kiro IDE and CLI), and `~/.gemini/config` (Antigravity IDE, App and CLI). `client-locations.md` lists the verified paths per surface, re-verified 2026-10-18, and what still needs a hands-on test. |
| Platforms | Windows and macOS. Linux is not tested. |
| Distribution | Plain files in the user-profile locations, no plugins. Until APM installs everything needed, a temporary script copies the needed files. The OneDrive folder `CodeFlow Agents` holds only the files the installed clients need and syncs them between laptop and desktop; it is never edited as a source. |
| Names and collisions | Packs and primary agents are named for the role. Names carry no artificial prefix; a qualifier inside a name, such as `build-python-mcp-server`, is fine. Two packs may ship the same name only with identical content, kept as one shared primitive in `Proj-Agent_Packs/shared-primitives/`; CI checks this. |
| Validation | Tier 1, deterministic: `Proj-Agent_Packs/tooling/validate_pack.py`, including an APM install for every target, on every pull request and weekly on Windows, macOS and Linux. Tier 2, AI: the generation engine creates or completes packs and checks them independently, as pull requests. Tier 3, keeping facts current: weekly watch workflows for vendor documentation (here), and for APM, draw.io and cloud icon releases (in Proj-Agent_Packs). Priority when choosing how: feasibility, then ease of use, then cost. |
| APM | 0.33.0, pinned in Proj-Agent_Packs CI; a weekly workflow reports newer releases. |
| Run records | Audit log and workflow records live in the user profile under the pack home, filed by repository. Nothing is written into the repository being worked on unless the user asks for committed evidence. |
| Pack home | One folder in the profile holds the controller, hook script, registry and state: `~/.code-workflow/` (approved). Hook commands reference it by absolute path. |
| Hooks | User-level only, and off until the user turns them on: `~/.claude/settings.json`, `~/.codex/hooks.json`, `~/.copilot/hooks/code-workflow.json`, `~/.kiro/hooks/` (documented for Kiro CLI V3; the IDE documents workspace hooks only), and `~/.gemini/config/hooks.json` for Antigravity. Codex requires the user to trust each hook once. The Copilot app documents no hooks. |
| Instructions | User-level only: `~/.claude/rules/code-workflow.md`, a marked section in `~/.codex/AGENTS.md`, `~/.copilot/instructions/code-workflow.instructions.md`, `~/.kiro/steering/`, and `~/.gemini/config/rules/` for Antigravity, where each file needs `trigger` frontmatter. The installer never creates `AGENTS.override.md`. The Copilot app keeps its own instructions inside the app. |
| Housekeeping | After every merge: stale branches deleted (automatic on merge in both repositories), temporary files and staging workspaces removed, and this file updated. |

## Orchestration decisions

Agreed 2026-10-18, answering the nine questions asked before step 5.

| # | Topic | Decision |
|---|---|---|
| 1 | Generator | Deterministic templates, filled from the clients detected on the desktop and the packs the user selected, so results are repeatable, free to run and testable. AI only helps write and review the templates. |
| 2 | Scope | One orchestrator per client, delegating only to agents installed in that client. Coordinating across clients is Code Conductor's job. |
| 3 | Selection | One selection file lists the chosen packs. It lives in the OneDrive folder, on Windows `C:\Users\<user>\OneDrive\Documents\CodeFlow Agents`, so laptop and desktop agree; the macOS path is set when the Mac is configured. Later the same list becomes APM's list of packages to install. |
| 4 | Where output goes | OneDrive holds the selection and the pulled packs. The orchestration is generated on each desktop, straight into each installed client's folders, and is never synced, because it depends on that desktop's tools. |
| 5 | Names | `<name>-<company>-<app>[-<version>]`, the version optional. Examples: `agentic-orchestrator-anthropic-claude-code`, `agentic-orchestrator-openai-codex`, `agentic-orchestrator-github-copilot`. The client part keeps orchestrators apart where clients read each other's folders. |
| 6 | Missing agents | Setup, and later APM, installs or updates the packs the selection lists, so the agents an orchestrator needs are present. When an orchestrator still lacks an agent, or its client cannot delegate, it works through rules, skills and step-by-step workflows instead and tells the user which pack to install, for example from a post-install hook. |
| 7 | Hooks | Generated where a client supports them, and off until the user turns them on. |
| 8 | Order | VS Code first: Claude Code, Codex and Copilot. Then Kiro and Antigravity, in either order. The apps (Antigravity app, GitHub Copilot app, VS Code's agent interface) must work too. |
| 9 | Home | Templates and the generator live in Code Workflow, the tool that runs on the desktop. Packs stay in Proj-Agent_Packs. |

### What the location check means for the templates

- **One orchestrator per engine.** Surfaces that share an engine share its folder, so `agentic-orchestrator-github-copilot` serves Copilot in VS Code, Copilot CLI and the Copilot app, and the Antigravity one serves its IDE, App and CLI.
- **Workflow steps are skills.** A skill is the one form every client runs as a slash command. Antigravity's legacy workflows stop working on 2026-10-19, Codex custom prompts are deprecated, and VS Code prompt files run only in the harness being retired.
- **Skills go to each client.** `~/.agents/skills` reaches only Codex and Copilot; Claude Code, Kiro and Antigravity each need their own copy.
- **Antigravity IDE has no documented custom agents yet.** Its App and CLI read `~/.gemini/config/agents/`; until the IDE does, the IDE gets the rules-and-skills fallback of decision 6.
- **VS Code's Copilot harness**, now becoming the default, reads `~/.copilot/agents` only when `github.copilot.chat.cli.customAgents.enabled` is on, and it defaults to off.
- **Kiro:** target the CLI V3 formats, which become the default with CLI 3.0 at the end of October 2026.

## What exists today

- **Packs:** 20 in `Proj-Agent_Packs`, all passing validation with an APM install for six targets. Five were generated from third-party skill collections (Notion, CloudFlare, Docker, Google Cloud, FinOps); 13 had their missing examples, templates and prompts filled; two were restructured. The Cloud Cybersecurity collection is parked (issue #22).
- **Shared primitives:** the draw.io skills shared by the AWS, Azure and Google Cloud packs, and the evaluation agent, four skills, security instruction and two prompts shared by the Python and TypeScript packs.
- **Code Workflow 0.1.0, pre-alpha:** controller, hooks, and an orchestrator agent for Claude Code, Codex and Copilot, installed per repository. The user-profile installer (v2) is not built yet.
- **Engine:** `Proj-Agent_Packs/tooling/generate_pack.py` generates and gap-fills packs headlessly and publishes them as pull requests.

## Plan

| # | Step | Status |
|---|---|---|
| 1 | Pack validator, tier 1 | Done, in Proj-Agent_Packs |
| 2 | Generation engine and the remaining packs | Done |
| 3 | Bind workflow completion to the reviewed content and the gates' results | Done, pull request #1; moving state into the pack home remains |
| 4 | Remove the remaining prompt-name collisions with qualified names | Done, Proj-Agent_Packs pull request #23; CI now fails on any install collision |
| 5 | **Orchestration templates, one per client:** how the orchestrator, handoffs, workflows, hooks, agents and skills are expressed in each client's own files, and a template that generates them from the selected packs | In progress: decisions agreed, client locations re-verified; VS Code templates first |
| 6 | Local setup: a script pulls the selected packs into the client locations and runs the generator (current success threshold) | After step 5 |
| 7 | APM pulls the packs and a minimal engine generates the orchestration (100%) | After step 6 |
| 8 | Verify Kiro and Antigravity, and the Copilot app, in the real clients | With steps 5 and 6; all of them are installed on the reference machine |
| 9 | Decide on the `CLAUDE_CODE_OAUTH_TOKEN` secret for generation on GitHub | Open, issue #21 in Proj-Agent_Packs |

## Progress log

- 2026-10-18: `Proj-Agent_Packs` created; the Python Distinguished Engineer pack restructured to prompt v2.1 and validated with an APM install for six targets.
- 2026-10-18: shared tooling in Proj-Agent_Packs; 15 packs converted to prompt v2.3. Six source folders were third-party skill collections that needed generation, not conversion.
- 2026-10-18: generation engine; Notion, CloudFlare, Docker, Google Cloud and FinOps generated, and 13 packs gap-filled, all as pull requests and merged.
- 2026-10-18: shared primitives for cloud diagrams and for Python and TypeScript; the Codex orchestrator moved out of the packs; client list extended to Antigravity, Kiro and the Copilot app, with their locations verified where documented.
- 2026-10-18: Code Workflow binds completion to reviewed evidence and fresh gates (pull request #1); prompt-name collisions removed in Proj-Agent_Packs (pull request #23).
- 2026-10-18: orchestration decisions agreed; every client's current locations re-verified against official documentation.

## Decisions still needed

- Whether regeneration of a failing pack may replace the source automatically, or always waits for approval of the diff (current design: waits, through a pull request).
- Whether setup may turn on `github.copilot.chat.cli.customAgents.enabled` in the user's VS Code settings, or only tells the user to, so that the Copilot orchestrator appears in VS Code's Copilot harness.
