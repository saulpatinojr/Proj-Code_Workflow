#!/usr/bin/env python3
"""Agent-client lifecycle hook: local audit records plus an opt-in Stop completion guard.

Works with Claude Code, Codex CLI, and GitHub Copilot hook payloads (all send JSON
on stdin with a cwd field; the event name is read from --event or the payload).
Stop and SubagentStop always emit a JSON object on stdout: Codex validates hook
output strictly, Claude Code treats {} as "no decision", Copilot ignores it.
The block decision is honored by Claude Code and Codex; elsewhere audit-only.

Fail-open by design: any missing file, unreadable state, or absent validator
results in exit 0 (allow). The hook can only block a Stop when ALL of these
are true: an active workflow exists, that workflow set enforce_stop=true at
init (--enforce-stop), the validator script exists, and validation fails.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def resolve_root(event: dict) -> Path:
    for candidate in (event.get("cwd"), os.environ.get("CLAUDE_PROJECT_DIR")):
        if candidate:
            return Path(candidate).resolve()
    return Path.cwd().resolve()


def finish(event_name: str, payload: dict | None = None) -> int:
    """Stop/SubagentStop must put JSON on stdout (Codex strict validation)."""
    if event_name in ("Stop", "SubagentStop"):
        print(json.dumps(payload or {}))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", default=None,
                        help="event name; when omitted, read from the payload (hook_event_name / hookEventName / event)")
    args = parser.parse_args()
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        event = {"raw_input_invalid": True, "raw_input": raw[:1000]}
    if not args.event:
        args.event = str(event.get("hook_event_name") or event.get("hookEventName") or event.get("event") or "unknown")
    aliases = {"sessionstart": "SessionStart", "sessionend": "SessionEnd", "subagentstart": "SubagentStart",
               "subagentstop": "SubagentStop", "agentstop": "Stop", "stop": "Stop"}
    args.event = aliases.get(args.event.replace("_", "").lower(), args.event)
    root = resolve_root(event)
    try:
        audit = root / ".agentic" / "audit"
        audit.mkdir(parents=True, exist_ok=True)
        record = {"recorded_at": datetime.now(timezone.utc).isoformat(), "event_argument": args.event, "event": event}
        with (audit / "claude-events.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    except OSError:
        pass  # auditing is best-effort; never break the session over a log line
    if args.event != "Stop":
        return finish(args.event)
    if event.get("stop_hook_active"):
        return finish(args.event)
    active = root / ".agentic" / "active-workflow.json"
    if not active.is_file():
        return finish(args.event)
    try:
        active_data = json.loads(active.read_text(encoding="utf-8"))
        workflow_id = active_data["workflow_id"]
        state_path = root / ".agentic" / "workflows" / workflow_id / "WORKFLOW.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, KeyError, json.JSONDecodeError):
        return finish(args.event)
    if not state.get("enforce_stop", False) or state.get("status") == "completed":
        return finish(args.event)
    validator = root / "tooling" / "workflow.py"
    if not validator.is_file():
        return finish(args.event)  # fail open: a mislocated install must never trap the session
    try:
        result = subprocess.run(
            [sys.executable, str(validator), "--root", str(root), "validate", "--workflow", workflow_id, "--check"],
            capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return finish(args.event)
    if result.returncode == 0:
        return finish(args.event)
    return finish(args.event, {
        "decision": "block",
        "reason": (f"Workflow {workflow_id} is not complete. Validate required subagent handoffs "
                   f"(python tooling/workflow.py validate --workflow {workflow_id}) or mark the "
                   f"workflow appropriately before ending the session."),
    })


if __name__ == "__main__":
    raise SystemExit(main())
