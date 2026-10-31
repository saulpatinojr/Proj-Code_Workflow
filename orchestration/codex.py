"""OpenAI Codex's orchestration, from templates/codex/: the orchestrator agent, the workflow skills, and hook
configuration that is written but not turned on. One orchestrator serves every surface that reads ~/.codex:
Codex CLI, its VS Code extension and the ChatGPT desktop app."""
from __future__ import annotations

import json
from pathlib import Path

import common

CLIENT = {
    "id": "codex",
    "label": "OpenAI Codex",
    "home_env": "CODEX_HOME",
    "home_default": ".codex",
    "orchestrator": "agentic-orchestrator-openai-codex",
    "start": "codex, then ask for the agentic-orchestrator-openai-codex agent",
    # What the earlier per-repository installer put in ~/.codex.
    "legacy": ("agents/claude-agentic-orchestrator.toml",),
}
TEMPLATES = common.TEMPLATES / "codex"
HOOK_EVENTS = ("SessionStart", "SubagentStart", "SubagentStop", "Stop")


def roster(home: Path) -> list:
    """The specialists installed in Codex, by name, with a one-line summary."""
    found = {}
    agents = home / "agents"
    if agents.is_dir():
        for name, description, _path in common.controller._scan_codex(agents):
            if not common.controller.is_orchestrator(name) and name not in found:
                found[name] = common.controller.capability_text(description, name)
    return sorted(found.items())


def skills_dir() -> Path:
    """Codex reads user skills from ~/.agents/skills, which follows the home folder, not CODEX_HOME."""
    return Path.home() / ".agents" / "skills"


def hook_settings(pack: Path, python: str) -> str:
    """A Codex hooks.json, ready to copy into ~/.codex/ when the user turns hooks on and trusts it with /hooks."""
    script = (pack / "hooks" / "claude_event.py").as_posix()

    def entry(event: str) -> list:
        return [{"hooks": [{"type": "command", "command": f'{python} "{script}" --event {event}', "timeout": 30}]}]

    return json.dumps({"hooks": {event: entry(event) for event in HOOK_EVENTS}}, indent=2) + "\n"


def plan(home: Path, pack: Path, python: str, windows: bool) -> dict:
    values = {
        "name": CLIENT["orchestrator"],
        "controller": common.controller_command(pack, python),
        "pack_home": pack.as_posix(),
        "roster": common.roster_text(roster(home)),
    }
    agent = common.render(common.read_text(TEMPLATES / "agent.toml"), values, "codex/agent.toml")
    if agent.count("'''") != 2:  # the instructions are one TOML literal string, so ''' may appear only around it
        raise SystemExit("codex/agent.toml: the rendered instructions contain ''', which would end the TOML string")
    files = {
        home / "agents" / f"{CLIENT['orchestrator']}.toml": agent,
        pack / "hooks" / "codex.hooks.json": hook_settings(pack, python),
    }
    files.update(common.skill_files(skills_dir(), values))
    return {path: text.encode("utf-8") for path, text in files.items()}
