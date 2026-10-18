"""Claude Code's orchestration, from templates/claude-code/: the orchestrator agent, the workflow skills,
a rule, and hook configuration that is written but not turned on."""
from __future__ import annotations

import json
from pathlib import Path

import common

CLIENT = {
    "id": "claude-code",
    "label": "Claude Code",
    "home_env": "CLAUDE_CONFIG_DIR",
    "home_default": ".claude",
    "orchestrator": "agentic-orchestrator-anthropic-claude-code",
    "start": "claude --agent agentic-orchestrator-anthropic-claude-code",
    # What the earlier per-repository installer put in ~/.claude.
    "legacy": ("agents/claude-agentic-orchestrator.md",
               *(f"skills/{name}" for name in common.controller.SKILL_SETS[1])),
}
TEMPLATES = common.TEMPLATES / "claude-code"


def roster(home: Path) -> list:
    """The specialists installed in Claude Code, by name, with a one-line summary."""
    found = {}
    agents = home / "agents"
    if agents.is_dir():
        for name, description, _path in common.controller._scan_claude(agents):
            if not common.controller.is_orchestrator(name) and name not in found:
                found[name] = common.controller.capability_text(description, name)
    return sorted(found.items())


def hook_settings(pack: Path, python: str) -> str:
    """The hooks key to merge into ~/.claude/settings.json when the user turns hooks on."""
    script = (pack / "hooks" / "claude_event.py").as_posix()

    def entry(event: str, timeout: int | None = None) -> list:
        hook = {"type": "command", "command": f'{python} "{script}" --event {event}'}
        if timeout:
            hook["timeout"] = timeout
        return [{"hooks": [hook]}]

    return json.dumps({"hooks": {"SessionStart": entry("SessionStart"), "SubagentStart": entry("SubagentStart"),
                                 "SubagentStop": entry("SubagentStop"), "Stop": entry("Stop", 30)}}, indent=2) + "\n"


def plan(home: Path, pack: Path, python: str, windows: bool) -> dict:
    tools = ["Read", "Glob", "Grep", "Bash"] + (["PowerShell"] if windows else []) + \
            ["WebFetch", "WebSearch", "Edit", "Write", "Skill", "Agent"]
    values = {
        "name": CLIENT["orchestrator"],
        "tools": ", ".join(tools),
        "skills": "\n".join(f"  - {name}" for name in common.skill_names()),
        "controller": common.controller_command(pack, python),
        "pack_home": pack.as_posix(),
        "roster": common.roster_text(roster(home)),
    }
    files = {
        home / "agents" / f"{CLIENT['orchestrator']}.md":
            common.render(common.read_text(TEMPLATES / "agent.md"), values, "claude-code/agent.md"),
        home / "rules" / "code-workflow.md":
            common.render(common.read_text(TEMPLATES / "rule.md"), values, "claude-code/rule.md"),
        pack / "hooks" / "claude-code.settings.json": hook_settings(pack, python),
    }
    files.update(common.skill_files(home / "skills", values))
    return {path: text.encode("utf-8") for path, text in files.items()}
