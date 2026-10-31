#!/usr/bin/env python3
"""Generate Code Workflow's orchestration for the AI clients installed on this computer.

The output depends only on the templates, the specialist agents installed in each client,
the platform and the folder paths, so a second run changes nothing (decision 1 in
docs/setup-design.md). Each client gets its own orchestrator, which delegates only to the
agents installed in that client (decision 2).

  python orchestration/generate.py                       every detected client that has a template
  python orchestration/generate.py --client claude-code  one client (claude-code, codex, github-copilot)
  python orchestration/generate.py --dry-run             show what would change; write nothing
  python orchestration/generate.py --replace-legacy      back up, then replace, what the earlier
                                                         per-repository installer put in the profile

What it writes:
  <pack home>/tooling/workflow.py, hooks/claude_event.py   the controller and hook, once per computer
  <pack home>/hooks/<client>.settings.json                 hook configuration, ready but not turned on
  <client home>/...                                        the orchestrator agent, its skills and a rule
                                                           (Codex and Copilot share ~/.agents/skills)
  <pack home>/generated.json                               every file written, with its sha256

The pack home is ~/.code-workflow, or CODE_WORKFLOW_HOME. A client's home follows that client's
own variable (CLAUDE_CONFIG_DIR, CODEX_HOME, COPILOT_HOME). The write rules are in safe_files.py; each
client's planner is a module beside this one.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling modules, also under python -I
import claude_code  # noqa: E402
import codex  # noqa: E402
import common  # noqa: E402
import github_copilot  # noqa: E402
import safe_files  # noqa: E402

MANIFEST = "generated.json"
CLIENTS = {module.CLIENT["id"]: module for module in (claude_code, codex, github_copilot)}
# Clients that are detected and reported, but have no template yet: (label, home variable, default home).
PLANNED = {
    "kiro": ("Kiro", "KIRO_HOME", ".kiro"),
    "antigravity": ("Google Antigravity", None, ".gemini/config"),
}


def pack_home() -> Path:
    moved = os.environ.get("CODE_WORKFLOW_HOME")
    return Path(moved) if moved else Path.home() / ".code-workflow"


def client_home(client: str) -> Path:
    spec = CLIENTS[client].CLIENT
    return common.home_of(spec["home_env"], spec["home_default"])


def plan_pack(pack: Path) -> dict:
    return {pack / "tooling" / "workflow.py": common.read_text(common.CONTROLLER_SOURCE).encode("utf-8"),
            pack / "hooks" / "claude_event.py": common.read_text(common.HOOK_SOURCE).encode("utf-8")}


def report(label: str, actions: list, conflicts: list) -> None:
    changed = [a for a in actions if a[0] != "unchanged"]
    print(f"{label}: {len(changed)} change(s), {len(actions) - len(changed)} unchanged, {len(conflicts)} conflict(s)")
    for kind, path, _data in changed:
        print(f"  {kind:<9} {path.as_posix()}")
    for path, reason in conflicts:
        print(f"  CONFLICT  {path.as_posix()}: {reason}")


def report_untemplated_clients() -> None:
    for label, env_var, default in (PLANNED[name] for name in sorted(PLANNED)):
        if common.home_of(env_var, default).is_dir():
            print(f"{label}: detected; its template is not built yet")


def report_legacy(legacy: list, replace_legacy: bool) -> None:
    verb = "Backing up and removing" if replace_legacy else "Left in place"
    print(f"  {verb}: {len(legacy)} item(s) from the earlier per-repository installer")
    for item in legacy:
        print(f"    {item.as_posix()}")
    if not replace_legacy:
        print("  Run with --replace-legacy to back them up and remove them.")


def generate_client(client: str, args: argparse.Namespace, pack: Path, manifest: dict, stamp: str) -> bool:
    """Plan, report and, unless this is a dry run, write one client's orchestration. False on conflicts."""
    module, home = CLIENTS[client], client_home(client)
    legacy = safe_files.legacy_present(module.CLIENT["legacy"], home, manifest)
    planned = module.plan(home, pack, args.python, os.name == "nt")
    actions, conflicts = safe_files.decide(planned, client, manifest, legacy, args.replace_legacy)
    report(f"{module.CLIENT['label']} {home.as_posix()}", actions, conflicts)
    if conflicts:
        print(f"  Nothing was written for {module.CLIENT['label']}.")
        return False
    if legacy:
        report_legacy(legacy, args.replace_legacy)
    if args.dry_run:
        return True
    if legacy and args.replace_legacy:
        destination = pack / "backup" / stamp / client
        safe_files.remove_legacy(legacy, home, destination)
        print(f"  Backup: {destination.as_posix()}")
    safe_files.apply(actions, manifest, client, home)
    print(f"  Start it with: {module.CLIENT['start']}")
    return True


def save_and_refresh_registry(pack: Path, manifest: dict) -> int:
    pack.mkdir(parents=True, exist_ok=True)
    (pack / MANIFEST).write_text(json.dumps({"version": 1, "files": dict(sorted(manifest.items()))}, indent=2) + "\n",
                                 encoding="utf-8")
    registry = subprocess.run([sys.executable, str(pack / "tooling" / "workflow.py"), "--root", str(pack), "registry"],
                              capture_output=True, text=True)
    print((registry.stdout or registry.stderr).strip())
    return registry.returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--client", action="append", choices=sorted(CLIENTS),
                        help="client to generate for (repeatable); default: every detected client with a template")
    parser.add_argument("--dry-run", action="store_true", help="report what would change and write nothing")
    parser.add_argument("--replace-legacy", action="store_true",
                        help="back up, then replace, files the earlier per-repository installer put in the profile")
    parser.add_argument("--python", default="python" if os.name == "nt" else "python3",
                        help="interpreter name the generated commands use (default: python on Windows, python3 elsewhere)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pack = pack_home()
    manifest_path = pack / MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")).get("files", {}) if manifest_path.is_file() else {}
    clients = args.client or [c for c in sorted(CLIENTS) if client_home(c).is_dir()]
    report_untemplated_clients()
    if not clients:
        print("No client with a template was found. Install Claude Code, Codex or GitHub Copilot, "
              "or name a client with --client.")
        return 1

    pack_actions, pack_conflicts = safe_files.decide(plan_pack(pack), "pack", manifest, [], False)
    report(f"Pack home {pack.as_posix()}", pack_actions, pack_conflicts)
    if pack_conflicts:
        print("The pack home has files Code Workflow did not write or that were changed; nothing was written.")
        return 1
    if not args.dry_run:
        safe_files.apply(pack_actions, manifest, "pack", pack)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    results = [generate_client(client, args, pack, manifest, stamp) for client in clients]
    if args.dry_run:
        print("Dry run: nothing was written.")
        return 0 if all(results) else 1
    registry_failed = save_and_refresh_registry(pack, manifest)
    return 0 if all(results) and not registry_failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
