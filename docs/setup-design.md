# Initial setup: design decisions

Status: agreed 2026-10-18, not yet built. This file is the contract for the installer rewrite. `client-locations.md` holds the verified folder locations it depends on, and `agent-pack-prompt.md` defines what a pack is.

## Goal

Install agent packs once, into the user profile, so every repository opened in VS Code can use them through the Claude Code, OpenAI Codex, and GitHub Copilot agent panes, on Windows and macOS. Code Workflow is the light sibling of Code Conductor; the same packs must serve both and must eventually be approved, official APM packages.

## Decisions

| Topic | Decision |
|---|---|
| What a pack is | The canonical layout from `agent-pack-prompt.md`: `apm.yml`, `.apm/agents/*.agent.md`, `.apm/skills/<name>/SKILL.md`, plus docs, tests, hooks, tooling, and generated vendor targets. One pack per role, holding a primary agent and optional specialists. |
| Source of truth | The canonical `.apm/` folder. Vendor files are generated from it and never edited by hand. The hand-maintained `user-claude/`, `user-codex/`, and `user-copilot/` folders in this repo are retired once the orchestrator is itself a pack. |
| Vendors in scope | Claude Code, Codex, GitHub Copilot, as used from the VS Code agent pane. The acceptance test for every vendor target is: the agent appears and runs in that pane. Gemini CLI targets may be generated but are not installed or tested. |
| Platforms | Windows and macOS. Linux is not tested. |
| Distribution | Plain files copied into the user-profile locations in `client-locations.md`. No plugins. Code Conductor owns richer packaging. |
| Validation | Three tiers. Tier 1 is deterministic and runs on every install: structure, required fields per vendor, real tool identifiers, skill name equals folder name, size limits, and contradictions such as an agent that forbids writing files but has a shell. Tier 2 is an AI review of a pack that proposes changes as a diff for the user to approve; it never edits a pack on its own. Tier 3 is an AI check of `client-locations.md` against current vendor documentation, run on demand, with a warning when the file is older than 30 days. Priority when choosing how: feasibility, then ease of use, then cost. |
| Pack sources | The canonical packs live in `OneDrive\Documents\ChatGPT\Agents`, versioned in the private GitHub repository `saulpatinojr/Proj-Agent_Packs`. OneDrive syncs the folder between laptop and desktop; on each machine the installer script reads from it, validates, and installs into the profile. Nothing in that folder is used directly by any client. |
| Regeneration engine | Lives in this repo. When a pack in the source folder fails validation against the master prompt or is inconsistent with the other packs, the engine regenerates it as a full package, using the master prompt and the options chosen in the installer run (vendors, platform). The regenerated pack is written to a staging folder, validated, and promoted only after the user approves the diff. |
| APM | Kept current: the installer checks for a newer APM release and offers the update. APM 0.33.0 installed 2026-10-18. |
| Run records | Audit log and workflow records live in the user profile under a pack home folder, filed by repository. Nothing is written into the repository being worked on unless the user asks for committed evidence. |
| Pack home | A single folder in the profile holds the controller, hook script, registry, and state: `~/.code-workflow/` (approved). Hook commands reference it by absolute path, because the per-repository `CLAUDE_PROJECT_DIR` variable cannot point at the pack. |
| Hooks | User-level only: `~/.claude/settings.json`, `~/.codex/hooks.json`, `~/.copilot/hooks/code-workflow.json`. Codex requires the user to trust each hook once. |
| Instructions | User-level only: `~/.claude/rules/code-workflow.md`, a marked section in `~/.codex/AGENTS.md`, and `~/.copilot/instructions/code-workflow.instructions.md`. The installer never creates `AGENTS.override.md`. |

## What exists today

- Three packs built with the master prompt. Two are in `OneDrive\Documents\ChatGPT\Agents` (microsoft-certified-trainer 1.0.0 with 5 agents, python-distinguished-engineer 2.0.0 with 5 agents). One is in `Downloads\Skills App` (codex-agentic-orchestrator 1.0.0, 1 agent, Codex target only). That folder has git initialised with no commits and no remote.
- Of the 25 agents installed in `~/.claude/agents`, 10 come from those packs and 13 have no canonical source. The installed python-pack agents are older than the pack's current output.
- APM CLI 0.26.0 is installed (0.33.0 available). `apm install -g` installs to user scope and reports full support for Claude Code and partial support for Codex and Copilot. What "partial" omits is not yet verified.
- Code Conductor's own pack uses the same canonical layout (`.apm/agents`, `.apm/skills`, `apm.yml`), so packs are interchangeable between the two projects.

## Build order

1. **Pack validator, tier 1.** A `workflow.py pack validate <path>` command that checks a canonical pack against the master prompt's required artifacts and each vendor's required fields. Run it on the three existing packs and fix what it finds.
2. **Installer v2.** Installs a validated pack into the user-profile locations, Windows and macOS, with the pack home folder, user-level hooks, and user-level instructions. Tested against a sandbox profile using `CLAUDE_CONFIG_DIR`, `CODEX_HOME`, and `COPILOT_HOME`, then in the real VS Code agent pane. The per-repository install path is removed.
3. **Orchestrator as a pack.** Rebuild the orchestrator with the master prompt, seeded from the existing Codex pack, with targets for all three vendors. Retire the hand-maintained vendor folders in this repo.
4. **Controller fixes.** Bind "completed" to the content that was reviewed: store evidence hashes when a handoff is validated, invalidate gate results when the tree changes, and move state into the pack home.
5. **Regeneration engine and remaining packs.** Build the engine, then use it to regenerate the 13 agents without a canonical source as full packs, one role at a time, with the installed file as reference material.
6. **Tiers 2 and 3.** AI pack review and AI location refresh, both producing diffs for approval.

## Decisions still needed

- Whether regeneration of a failing pack may replace the source automatically, or always waits for approval of the diff (current design: waits).
