# Pack review: Python Distinguished Engineer (version 2.0.0)

Reviewed 2026-10-18 from `OneDrive - hybridcloudworks.com\Content\Agents\Agent Packs\Python Distinguished Engineer Agent`. This review drove version 2 of `agent-pack-prompt.md`.

## What is sound

- The canonical source under `.apm/` is identical to the copy already in the pack repository. Five agents, eighteen skills, every skill folder name equals its `name`.
- The pack's own validator passes (855 checks) and its 21 offline tests pass when run on a copy with PyYAML installed.
- Archive checksums verify, 27 of 27.
- Agent frontmatter is valid for the vendors it targets. The Claude list of tools, the Copilot aliases (read, search, edit, execute, agent) with `user-invocable`, and the Gemini fields (`kind: local`, tool names, `max_turns`) are all documented forms.
- The Copilot hook file uses the documented shape (`version`, camelCase events, `bash` and `powershell` commands, `timeoutSec`).

## What must change

1. **Built for project scope, not user scope.** Every vendor target's `INSTALL.md` says to merge it into a project. Targets carry repo-root `shared/`, `docs/`, `tests/`, and `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `copilot-instructions.md` at the root. Hooks call `.github/hooks/scripts/hook_runner.py`, a path that only exists inside a repository. None of this works from the user profile, which is the install model Code Workflow uses.
2. **The manifest uses fields APM does not have.** `source`, `agents`, and `skills` are not top-level `apm.yml` fields and are ignored. `targets` is missing, so APM has nothing to deploy to without a flag.
3. **Hand-built vendor targets duplicate what APM generates.** `targets/<vendor>/` holds files APM derives from `.apm/` at install time. Keeping both means two sources that drift.
4. **Stale leftovers.** Four top-level vendor folders (`claude-code`, `gemini-cli`, `github-copilot`, `openai-codex`) are August copies that differ from `targets/` in 47 to 61 files each. A `python-distinguished-engineer-full-pack.zip` from August sits at the root beside the current one in `dist/`. Three `__pycache__` folders are present.
5. **The artifact catalog embeds every file.** `AGENT-PACK-README.md` is 1 MB because it repeats the full contents of the pack. The pack is the files; the catalog should list them.
6. **Instructions and prompts are not APM primitives.** They sit in root `instructions/` and `prompts/` folders. APM reads `.apm/instructions/*.instructions.md` (with `applyTo`) and `.apm/prompts/*.prompt.md`, and from those it generates `.github/instructions`, `.claude/rules`, `.kiro/steering`, and the Codex and Gemini context files.
7. **Kiro is missing.** Code Conductor targets Kiro; the pack has no Kiro agents, steering, or hooks.
8. **Distribution archives are committed build output.** 28 zip files that any build regenerates.

## What is unverified

- Whether Copilot agents installed to `~/.copilot/agents` appear in VS Code Copilot-harness sessions with default settings.
- Whether the pack's five agents behave as documented when actually invoked. The validation report says so itself: live discovery and invocation in the four clients "remain unverified".
