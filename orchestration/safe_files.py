"""The generator's write rules: what may be created, updated, replaced or removed, and how.

A file is overwritten only when the generator wrote it and nobody has changed it since. Files from
the earlier per-repository installer are replaced only on request, after a backup.
"""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

LEGACY_REASON = ("installed by the earlier per-repository installer; "
                 "run with --replace-legacy to back it up and replace it")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def within(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def legacy_present(legacy_paths: tuple, home: Path, manifest: dict) -> list:
    """Legacy items that exist and that the generator has never taken over."""
    found = []
    for rel in legacy_paths:
        path = home / rel
        if path.exists() and not any(within(Path(key), path) for key in manifest):
            found.append(path)
    return found


def judge_existing(current: str, wanted: str, recorded: str | None, in_legacy: bool):
    if current == wanted:
        return "unchanged", None
    if recorded == current:
        return "update", None
    if recorded:
        reason = "changed since Code Workflow wrote it"
    else:
        reason = LEGACY_REASON if in_legacy else "not written by Code Workflow"
    return None, reason


def decide_file(path: Path, data: bytes, manifest: dict, in_legacy: bool, replace_legacy: bool):
    """Return (action, None) when the planned file may be written, or (None, reason) when it may not."""
    if in_legacy and replace_legacy:
        return "replace", None  # the legacy item is removed before writing, so the file is written afresh
    if not path.exists():
        return "create", None
    if path.is_dir():
        return None, "a folder is in the way"
    recorded = manifest.get(path.as_posix(), {}).get("sha256")
    return judge_existing(sha(path.read_bytes()), sha(data), recorded, in_legacy)


def stale_actions(planned: dict, owner: str, manifest: dict) -> list:
    """Files this owner wrote before but no longer generates: removed when unchanged, otherwise left alone."""
    actions = []
    for key, entry in sorted(manifest.items()):
        path = Path(key)
        if entry.get("owner") != owner or path in planned or not path.is_file():
            continue
        unchanged = sha(path.read_bytes()) == entry["sha256"]
        actions.append(("remove" if unchanged else "keep", path, None))
    return actions


def decide(planned: dict, owner: str, manifest: dict, legacy: list, replace_legacy: bool):
    actions, conflicts = [], []
    for path, data in sorted(planned.items()):
        in_legacy = any(within(path, item) for item in legacy)
        action, reason = decide_file(path, data, manifest, in_legacy, replace_legacy)
        if action:
            actions.append((action, path, data))
        else:
            conflicts.append((path, reason))
    return actions + stale_actions(planned, owner, manifest), conflicts


def remove_legacy(legacy: list, home: Path, destination: Path) -> None:
    """Copy each legacy item under destination, keeping its path below the client home, then remove it."""
    for item in legacy:
        target = destination / item.relative_to(home)
        target.parent.mkdir(parents=True, exist_ok=True)
        if item.is_dir():
            shutil.copytree(item, target)
            shutil.rmtree(item)
        else:
            shutil.copy2(item, target)
            item.unlink()


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
