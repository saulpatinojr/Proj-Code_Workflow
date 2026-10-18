"""Paths and helpers shared by the orchestration generator and its client planners."""
from __future__ import annotations

import importlib.util
import os
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
TEMPLATES = HERE / "templates"
SKILLS = HERE / "skills"
CONTROLLER_SOURCE = REPO / "repo-root" / "tooling" / "workflow.py"
HOOK_SOURCE = REPO / "repo-root" / "hooks" / "claude_event.py"
PLACEHOLDER = re.compile(r"\{\{([a-z_]+)\}\}")


def _load_controller():
    """The controller's own scanners decide what counts as an installed agent, so both tools agree."""
    spec = importlib.util.spec_from_file_location("code_workflow_controller", CONTROLLER_SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


controller = _load_controller()


def home_of(env_var: str | None, default: str) -> Path:
    moved = os.environ.get(env_var) if env_var else None
    return Path(moved) if moved else Path.home() / default


def read_text(path: Path) -> str:
    """Templates are read with LF line endings, whatever the checkout uses, so output is identical everywhere."""
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def render(template: str, values: dict, source: str) -> str:
    def swap(match):
        key = match.group(1)
        if key not in values:
            raise SystemExit(f"{source}: unknown placeholder {{{{{key}}}}}")
        return values[key]
    return PLACEHOLDER.sub(swap, template)


def controller_command(pack: Path, python: str) -> str:
    return f'{python} "{(pack / "tooling" / "workflow.py").as_posix()}"'


def roster_text(roster: list) -> str:
    if not roster:
        return ("No specialist agents are installed in this client yet. "
                "Install agent packs, then run the generator again.")
    return "\n".join(f"- `{name}`: {summary}" for name, summary in roster)


def skill_names() -> list:
    return sorted(path.name for path in SKILLS.iterdir() if path.is_dir())


def skill_files(target: Path, values: dict) -> dict:
    """Every workflow skill file, rendered, under the client's skills folder."""
    files = {}
    for path in sorted(SKILLS.rglob("*")):
        if path.is_file():
            relative = path.relative_to(SKILLS)
            files[target / relative] = render(read_text(path), values, f"skills/{relative.as_posix()}")
    return files
