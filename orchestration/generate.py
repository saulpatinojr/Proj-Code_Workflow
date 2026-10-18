#!/usr/bin/env python3
"""Generate Code Workflow's orchestration for the AI clients installed on this computer.

The output depends only on the templates, the specialist agents installed in each client,
the platform and the folder paths, so a second run changes nothing (decision 1 in
docs/setup-design.md). Each client gets its own orchestrator, which delegates only to the
agents installed in that client (decision 2).

  python orchestration/generate.py                       every detected client that has a template
  python orchestration/generate.py --client claude-code  one client
  python orchestration/generate.py --dry-run             show what would change; write nothing
  python orchestration/generate.py --replace-legacy      back up, then replace, what the earlier
                                                         per-repository installer put in the profile

What it writes:
  <pack home>/tooling/workflow.py, hooks/claude_event.py   the controller and hook, once per computer
  <pack home>/hooks/<client>.settings.json                 hook configuration, ready but not turned on
  <client home>/...                                        the orchestrator agent, its skills and a rule
  <pack home>/generated.json                               every file written, with its sha256

The pack home is ~/.code-workflow, or CODE_WORKFLOW_HOME. A client's home follows that client's
own variable (CLAUDE_CONFIG_DIR for Claude Code). A file is overwritten only when this tool wrote
it and nobody has changed it since; anything else stops that client and is reported.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
TEMPLATES = HERE / "templates"
SKILLS = HERE / "skills"
CONTROLLER_SOURCE = REPO / "repo-root" / "tooling" / "workflow.py"
HOOK_SOURCE = REPO / "repo-root" / "hooks" / "claude_event.py"
MANIFEST = "generated.json"
PLACEHOLDER = re.compile(r"\{\{([a-z_]+)\}\}")


def _load_controller():
    """The controller's own scanners decide what counts as an installed agent, so both tools agree."""
    spec = importlib.util.spec_from_file_location("code_workflow_controller", CONTROLLER_SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


controller = _load_controller()

# Clients with a template. The legacy paths are what the earlier per-repository installer put in the
# client's home; they are replaced only with --replace-legacy, after a backup.
CLIENTS = {
    "claude-code": {
        "label": "Claude Code",
        "home_env": "CLAUDE_CONFIG_DIR",
        "home_default": ".claude",
        "orchestrator": "agentic-orchestrator-anthropic-claude-code",
        "legacy": ("agents/claude-agentic-orchestrator.md",
                   *(f"skills/{name}" for name in controller.SKILL_SETS[1])),
    },
}
# Clients that are detected and reported, but have no template yet.
PLANNED = {
    "codex": ("OpenAI Codex", "CODEX_HOME", ".codex"),
    "github-copilot": ("GitHub Copilot", "COPILOT_HOME", ".copilot"),
    "kiro": ("Kiro", "KIRO_HOME", ".kiro"),
    "antigravity": ("Google Antigravity", None, ".gemini/config"),
}


def pack_home() -> Path:
    moved = os.environ.get("CODE_WORKFLOW_HOME")
    return Path(moved) if moved else Path.home() / ".code-workflow"


def home_of(env_var: str | None, default: str) -> Path:
    moved = os.environ.get(env_var) if env_var else None
    return Path(moved) if moved else Path.home() / default


def client_home(client: str) -> Path:
    return home_of(CLIENTS[client]["home_env"], CLIENTS[client]["home_default"])


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


# ---- Claude Code ---------------------------------------------------------------

def claude_roster(home: Path) -> list:
    found = {}
    agents = home / "agents"
    if agents.is_dir():
        for name, description, _path in controller._scan_claude(agents):
            if not controller.is_orchestrator(name) and name not in found:
                found[name] = controller.capability_text(description, name)
    return sorted(found.items())


def claude_hook_settings(pack: Path, python: str) -> str:
    """The hooks key to merge into ~/.claude/settings.json when the user turns hooks on (decision 7)."""
    script = (pack / "hooks" / "claude_event.py").as_posix()

    def entry(event: str, timeout: int | None = None) -> list:
        hook = {"type": "command", "command": f'{python} "{script}" --event {event}'}
        if timeout:
            hook["timeout"] = timeout
        return [{"hooks": [hook]}]

    return json.dumps({"hooks": {"SessionStart": entry("SessionStart"), "SubagentStart": entry("SubagentStart"),
                                 "SubagentStop": entry("SubagentStop"), "Stop": entry("Stop", 30)}}, indent=2) + "\n"


def plan_claude_code(home: Path, pack: Path, python: str, windows: bool) -> dict:
    spec = CLIENTS["claude-code"]
    skill_names = sorted(path.name for path in SKILLS.iterdir() if path.is_dir())
    tools = ["Read", "Glob", "Grep", "Bash"] + (["PowerShell"] if windows else []) + \
            ["WebFetch", "WebSearch", "Edit", "Write", "Skill", "Agent"]
    values = {
        "name": spec["orchestrator"],
        "tools": ", ".join(tools),
        "skills": "\n".join(f"  - {name}" for name in skill_names),
        "controller": controller_command(pack, python),
        "pack_home": pack.as_posix(),
        "roster": roster_text(claude_roster(home)),
    }
    files = {
        home / "agents" / f"{spec['orchestrator']}.md":
            render(read_text(TEMPLATES / "claude-code" / "agent.md"), values, "claude-code/agent.md"),
        home / "rules" / "code-workflow.md":
            render(read_text(TEMPLATES / "claude-code" / "rule.md"), values, "claude-code/rule.md"),
        pack / "hooks" / "claude-code.settings.json": claude_hook_settings(pack, python),
    }
    for path in sorted(SKILLS.rglob("*")):
        if path.is_file():
            relative = path.relative_to(SKILLS)
            files[home / "skills" / relative] = render(read_text(path), values, f"skills/{relative.as_posix()}")
    return {path: text.encode("utf-8") for path, text in files.items()}


PLANNERS = {"claude-code": plan_claude_code}


def plan_pack(pack: Path) -> dict:
    return {pack / "tooling" / "workflow.py": read_text(CONTROLLER_SOURCE).encode("utf-8"),
            pack / "hooks" / "claude_event.py": read_text(HOOK_SOURCE).encode("utf-8")}


# ---- deciding and writing --------------------------------------------------------

def within(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def legacy_present(client: str, home: Path, manifest: dict) -> list:
    """Legacy items that exist and that this tool has never taken over."""
    found = []
    for rel in CLIENTS[client]["legacy"]:
        path = home / rel
        if path.exists() and not any(within(Path(key), path) for key in manifest):
            found.append(path)
    return found


def decide(planned: dict, owner: str, manifest: dict, legacy: list, replace_legacy: bool):
    actions, conflicts = [], []
    for path, data in sorted(planned.items()):
        in_legacy = any(within(path, item) for item in legacy)
        if in_legacy and replace_legacy:
            # The legacy item is removed before writing, so this file is always written afresh.
            actions.append(("replace", path, data))
            continue
        if not path.exists():
            actions.append(("create", path, data))
            continue
        if path.is_dir():
            conflicts.append((path, "a folder is in the way"))
            continue
        current = sha(path.read_bytes())
        if current == sha(data):
            actions.append(("unchanged", path, data))
            continue
        recorded = manifest.get(path.as_posix(), {}).get("sha256")
        if recorded == current:
            actions.append(("update", path, data))
        elif recorded:
            conflicts.append((path, "changed since Code Workflow wrote it"))
        elif in_legacy:
            conflicts.append((path, "installed by the earlier per-repository installer; "
                                    "run with --replace-legacy to back it up and replace it"))
        else:
            conflicts.append((path, "not written by Code Workflow"))
    for key, entry in sorted(manifest.items()):
        path = Path(key)
        if entry.get("owner") != owner or path in planned or not path.is_file():
            continue
        if sha(path.read_bytes()) == entry["sha256"]:
            actions.append(("remove", path, None))
        else:
            actions.append(("keep", path, None))  # no longer generated, but changed by someone: left alone
    return actions, conflicts


def backup(item: Path, base: Path, destination: Path) -> None:
    target = destination / item.relative_to(base)
    target.parent.mkdir(parents=True, exist_ok=True)
    if item.is_dir():
        shutil.copytree(item, target)
    else:
        shutil.copy2(item, target)


def remove_empty_parents(path: Path, stop: Path) -> None:
    parent = path.parent
    while within(parent, stop) and parent != stop:
        try:
            parent.rmdir()
        except OSError:
            return
        parent = parent.parent


def apply(actions: list, manifest: dict, owner: str, stop: Path) -> None:
    for kind, path, data in actions:
        if kind in ("create", "update", "replace"):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        elif kind == "remove":
            path.unlink()
            remove_empty_parents(path, stop)
        if kind in ("remove", "keep"):
            manifest.pop(path.as_posix(), None)
        else:
            manifest[path.as_posix()] = {"sha256": sha(data), "owner": owner}


def report(label: str, actions: list, conflicts: list) -> None:
    changed = [a for a in actions if a[0] != "unchanged"]
    print(f"{label}: {len(changed)} change(s), {len(actions) - len(changed)} unchanged, {len(conflicts)} conflict(s)")
    for kind, path, _data in changed:
        print(f"  {kind:<9} {path.as_posix()}")
    for path, reason in conflicts:
        print(f"  CONFLICT  {path.as_posix()}: {reason}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--client", action="append", choices=sorted(CLIENTS),
                        help="client to generate for (repeatable); default: every detected client with a template")
    parser.add_argument("--dry-run", action="store_true", help="report what would change and write nothing")
    parser.add_argument("--replace-legacy", action="store_true",
                        help="back up, then replace, files the earlier per-repository installer put in the profile")
    parser.add_argument("--python", default="python" if os.name == "nt" else "python3",
                        help="interpreter name the generated commands use (default: python on Windows, python3 elsewhere)")
    args = parser.parse_args()

    pack = pack_home()
    manifest_path = pack / MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")).get("files", {}) if manifest_path.is_file() else {}
    clients = args.client or [c for c in sorted(CLIENTS) if client_home(c).is_dir()]
    for name, (label, env_var, default) in sorted(PLANNED.items()):
        if home_of(env_var, default).is_dir():
            print(f"{label}: detected; its template is not built yet")
    if not clients:
        print("No client with a template was found. Install Claude Code, or name a client with --client.")
        return 1

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pack_actions, pack_conflicts = decide(plan_pack(pack), "pack", manifest, [], False)
    report(f"Pack home {pack.as_posix()}", pack_actions, pack_conflicts)
    if pack_conflicts:
        print("The pack home has files Code Workflow did not write or that were changed; nothing was written.")
        return 1
    if not args.dry_run:
        apply(pack_actions, manifest, "pack", pack)

    failed = False
    for client in clients:
        home = client_home(client)
        legacy = legacy_present(client, home, manifest)
        planned = PLANNERS[client](home, pack, args.python, os.name == "nt")
        actions, conflicts = decide(planned, client, manifest, legacy, args.replace_legacy)
        label = CLIENTS[client]["label"]
        report(f"{label} {home.as_posix()}", actions, conflicts)
        if conflicts:
            failed = True
            print(f"  Nothing was written for {label}.")
            continue
        if legacy:
            verb = "Backing up and removing" if args.replace_legacy else "Left in place"
            print(f"  {verb}: {len(legacy)} item(s) from the earlier per-repository installer")
            for item in legacy:
                print(f"    {item.as_posix()}")
            if not args.replace_legacy:
                print("  Run with --replace-legacy to back them up and remove them.")
        if args.dry_run:
            continue
        if legacy and args.replace_legacy:
            destination = pack / "backup" / stamp / client
            for item in legacy:
                backup(item, home, destination)
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            print(f"  Backup: {destination.as_posix()}")
        apply(actions, manifest, client, home)
        print(f"  Start it with: claude --agent {CLIENTS[client]['orchestrator']}")

    if args.dry_run:
        print("Dry run: nothing was written.")
        return 1 if failed else 0
    pack.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({"version": 1, "files": dict(sorted(manifest.items()))}, indent=2) + "\n",
                             encoding="utf-8")
    registry = subprocess.run([sys.executable, str(pack / "tooling" / "workflow.py"), "--root", str(pack), "registry"],
                              capture_output=True, text=True)
    print((registry.stdout or registry.stderr).strip())
    return 1 if failed or registry.returncode else 0


if __name__ == "__main__":
    raise SystemExit(main())
