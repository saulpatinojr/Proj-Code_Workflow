"""GitHub Copilot's orchestration, from templates/github-copilot/: the orchestrator agent, the workflow skills,
an instructions file, and hook configuration that is written but not turned on. One orchestrator serves every
surface that reads ~/.copilot: Copilot CLI, the GitHub Copilot app and VS Code's Copilot harness."""
from __future__ import annotations

import json
import os
from pathlib import Path

import common

CLIENT = {
    "id": "github-copilot",
    "label": "GitHub Copilot",
    "home_env": "COPILOT_HOME",
    "home_default": ".copilot",
    "orchestrator": "agentic-orchestrator-github-copilot",
    "start": "copilot --agent agentic-orchestrator-github-copilot, or pick it with /agent in the Copilot app",
    # What the earlier per-repository installer put in ~/.copilot.
    "legacy": ("agents/claude-agentic-orchestrator.agent.md",),
}
TEMPLATES = common.TEMPLATES / "github-copilot"
# Copilot's tool aliases (docs/client-locations.md); `agent` runs the custom agents as subagents.
TOOLS = ("read", "search", "edit", "execute", "web", "agent", "todo")
# Copilot event name -> the name claude_event.py records, so every client's audit log reads the same.
HOOK_EVENTS = {"sessionStart": "SessionStart", "subagentStart": "SubagentStart",
               "subagentStop": "SubagentStop", "agentStop": "Stop"}


def roster(home: Path) -> list:
    """The specialists installed in Copilot, by name, with a one-line summary."""
    found = {}
    agents = home / "agents"
    if agents.is_dir():
        for name, description, _path in common.controller._scan_copilot(agents):
            if not common.controller.is_orchestrator(name) and name not in found:
                found[name] = common.controller.capability_text(description, name)
    return sorted(found.items())


def skills_dir(home: Path) -> Path:
    """~/.agents/skills reaches Copilot CLI, the app and VS Code, but the CLI stops reading it when COPILOT_HOME
    is set, so a moved home gets its own copy."""
    return home / "skills" if os.environ.get(CLIENT["home_env"]) else Path.home() / ".agents" / "skills"


def hook_settings(pack: Path, python: str) -> str:
    """A Copilot hooks file, ready to copy into ~/.copilot/hooks/ when the user turns hooks on."""
    script = (pack / "hooks" / "claude_event.py").as_posix()

    def entry(event: str) -> list:
        command = f'{python} "{script}" --event {event}'
        return [{"type": "command", "bash": command, "powershell": command, "timeoutSec": 30}]

    return json.dumps({"version": 1, "hooks": {name: entry(event) for name, event in HOOK_EVENTS.items()}},
                      indent=2) + "\n"


def plan(home: Path, pack: Path, python: str, windows: bool) -> dict:
    values = {
        "name": CLIENT["orchestrator"],
        "tools": ", ".join(f'"{tool}"' for tool in TOOLS),
        "controller": common.controller_command(pack, python),
        "pack_home": pack.as_posix(),
        "roster": common.roster_text(roster(home)),
    }
    files = {
        home / "agents" / f"{CLIENT['orchestrator']}.agent.md":
            common.render(common.read_text(TEMPLATES / "agent.md"), values, "github-copilot/agent.md"),
        home / "instructions" / "code-workflow.instructions.md":
            common.render(common.read_text(TEMPLATES / "instructions.md"), values, "github-copilot/instructions.md"),
        pack / "hooks" / "github-copilot.hooks.json": hook_settings(pack, python),
    }
    files.update(common.skill_files(skills_dir(home), values))
    return {path: text.encode("utf-8") for path, text in files.items()}
