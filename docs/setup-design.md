# Setup: design decisions and status

Agreed 2026-10-18 and updated as work lands; last updated 2026-10-18. `client-locations.md` holds the verified folder locations this plan depends on, and `agent-pack-prompt.md` defines what a pack is.

## Goal

Install agent packs once, into the user profile, so every repository can use them in the clients the user works in, on Windows and macOS:

- VS Code, with the Claude Code, Codex and GitHub Copilot agent panes;
- Google Antigravity, both the IDE and the app;
- Kiro, the IDE;
- the GitHub Copilot app.

Code Workflow is the light sibling of Code Conductor; the same packs serve both and must eventually be approved, official APM packages.

## How success is measured

- **Current threshold:** scripts pull the selected agent packs from GitHub into the installed clients' folder locations, and the orchestration for those clients is generated locally.
- **100%:** APM pulls the selected agent packs, and a minimal engine, perhaps a workflow, generates the customized orchestration for the clients installed on that desktop.

## Decisions

| Topic | Decision |
|---|---|
| What a pack is | The canonical layout of `agent-pack-prompt.md` (version 2.3): `apm.yml` and `.apm/` with agents, skills, instructions and prompts, plus docs, tests, hook samples and tooling. APM generates every client's files at install time; there are no hand-built vendor targets, and build archives are never committed. One pack per role, with one primary agent and optional specialists. |
| Source of truth | The public GitHub repository `saulpatinojr/Proj-Agent_Packs`. Every change arrives as a pull request; merging it is the approval. |
| Orchestrators | Not packs. An orchestrator is a client's main coordinating agent. It is generated for each desktop from the tools found there and the packs, agents and skills the user selected, using a template per client. The Codex seed is kept unchanged in `Proj-Agent_Packs/orchestrators/` as reference. Orchestration templates are the current priority. |
| Clients and their folders | Each client reads its own home folder: `~/.claude`, `~/.codex` with `~/.agents/skills`, `~/.copilot` (VS Code, Copilot CLI and the Copilot app), `~/.kiro`, and `~/.gemini` for Antigravity. `client-locations.md` lists the verified paths and the gaps still to verify, such as where Antigravity defines custom agents and hooks. |
| Platforms | Windows and macOS. Linux is not tested. |
| Distribution | Plain files in the user-profile locations, no plugins. Until APM installs everything needed, a temporary script copies the needed files. The OneDrive folder `CodeFlow Agents` holds only the files the installed clients need and syncs them between laptop and desktop; it is never edited as a source. |
| Names and collisions | Packs and primary agents are named for the role. Names carry no artificial prefix; a qualifier inside a name, such as `build-python-mcp-server`, is fine. Two packs may ship the same name only with identical content, kept as one shared primitive in `Proj-Agent_Packs/shared-primitives/`; CI checks this. |
| Validation | Tier 1, deterministic: `Proj-Agent_Packs/tooling/validate_pack.py`, including an APM install for every target, on every pull request and weekly on Windows, macOS and Linux. Tier 2, AI: the generation engine creates or completes packs and checks them independently, as pull requests. Tier 3, keeping facts current: weekly watch workflows for vendor documentation (here), and for APM, draw.io and cloud icon releases (in Proj-Agent_Packs). Priority when choosing how: feasibility, then ease of use, then cost. |
| APM | 0.33.0, pinned in Proj-Agent_Packs CI; a weekly workflow reports newer releases. |
| Run records | Audit log and workflow records live in the user profile under the pack home, filed by repository. Nothing is written into the repository being worked on unless the user asks for committed evidence. |
| Pack home | One folder in the profile holds the controller, hook script, registry and state: `~/.code-workflow/` (approved). Hook commands reference it by absolute path. |
| Hooks | User-level only: `~/.claude/settings.json`, `~/.codex/hooks.json`, `~/.copilot/hooks/code-workflow.json`, and `~/.kiro/hooks/` for Kiro CLI. Codex requires the user to trust each hook once. Antigravity's hook location is not yet verified. |
| Instructions | User-level only: `~/.claude/rules/code-workflow.md`, a marked section in `~/.codex/AGENTS.md`, `~/.copilot/instructions/code-workflow.instructions.md`, `~/.kiro/steering/`, and `~/.gemini/config/rules/` for Antigravity. The installer never creates `AGENTS.override.md`. |
| Housekeeping | After every merge: stale branches deleted (automatic on merge in both repositories), temporary files and staging workspaces removed, and this file updated. |

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
| 3 | Bind workflow completion to the reviewed content and the gates' results | Done in Code Workflow pull request #1; moving state into the pack home remains |
| 4 | Remove the remaining prompt-name collisions with qualified names | In progress |
| 5 | **Orchestration templates, one per client:** how the orchestrator, handoffs, workflows, hooks, agents and skills are expressed in each client's own files, and a template that generates them from the selected packs | Next, priority |
| 6 | Local setup: a script pulls the selected packs into the client locations and runs the generator (current success threshold) | After step 5 |
| 7 | APM pulls the packs and a minimal engine generates the orchestration (100%) | After step 6 |
| 8 | Verify Kiro and Antigravity, and the Copilot app, in the real clients | With steps 5 and 6 |
| 9 | Decide on the `CLAUDE_CODE_OAUTH_TOKEN` secret for generation on GitHub | Open, issue #21 in Proj-Agent_Packs |

## Progress log

- 2026-10-18: `Proj-Agent_Packs` created; the Python Distinguished Engineer pack restructured to prompt v2.1 and validated with an APM install for six targets.
- 2026-10-18: shared tooling in Proj-Agent_Packs; 15 packs converted to prompt v2.3. Six source folders were third-party skill collections that needed generation, not conversion.
- 2026-10-18: generation engine; Notion, CloudFlare, Docker, Google Cloud and FinOps generated, and 13 packs gap-filled, all as pull requests and merged.
- 2026-10-18: shared primitives for cloud diagrams and for Python and TypeScript; the Codex orchestrator moved out of the packs; client list extended to Antigravity, Kiro and the Copilot app, with their locations verified where documented.
- 2026-10-18: Code Workflow binds completion to reviewed evidence and fresh gates (pull request #1).

## Decisions still needed

- Whether regeneration of a failing pack may replace the source automatically, or always waits for approval of the diff (current design: waits, through a pull request).
- The open questions for orchestration templates, recorded when step 5 starts.
