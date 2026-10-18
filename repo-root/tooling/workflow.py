#!/usr/bin/env python3
"""Code Workflow controller: create, discover, gate, validate, and export agentic workflow state.

Code Workflow runs multi-agent workflows INSIDE one AI client (Claude Code, Codex CLI,
or GitHub Copilot) through that client's native subagents. It never spawns other
providers, manages worktrees, or issues merge/readiness decisions; that is Code
Conductor's job. See README.md "Boundaries".

Path model (two anchors, never confused):
  PACK_HOME   = the directory this script lives in (tooling/). The agent registry and
                optional gates.json live beside the script and always resolve here.
  PROJECT_DIR = the repository the workflow runs in. Resolved in order:
                --root flag > CLAUDE_PROJECT_DIR env > git toplevel > cwd.
                All runtime state (.agentic/) is created under PROJECT_DIR.

Agent-pack adapters: discovery scans every installed agent ecosystem --
  claude-code    : <repo>/.claude/agents and ~/.claude/agents   (*.md, frontmatter name)
  github-copilot : <repo>/.github/agents and ~/.copilot/agents  (*.agent.md / *.md)
  codex          : <repo>/.codex/agents and ~/.codex/agents     (*.toml, name = "...")
Same agent name found in several ecosystems = one registry entry, all paths kept.

Commands:
  registry   regenerate tooling/agent-registry.yml from installed agents
  discover   report which registry agents are installed, where, and for which clients
  init       create .agentic/workflows/<id>/ before any delegation
  gates      run deterministic repository checks (terraform, ansible, npm, pytest, custom)
  validate   check required handoffs and gates; exit 0 only when the workflow is clean
  export     write a Code Conductor RunManifest-compatible JSON for the workflow
  doctor     check installation health (clients, skills, hooks, registry, gitignore)
  status     print a workflow's WORKFLOW.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

VERSION = "0.1.0"
PACK_HOME = Path(__file__).resolve().parent
REGISTRY = PACK_HOME / "agent-registry.yml"
GATES_CONFIG = PACK_HOME / "gates.json"
ORCHESTRATOR_NAME = "claude-agentic-orchestrator"
RISK_CLASSES = ("R0", "R1", "R2", "R3", "R4")
EXPECTED_SKILLS = (
    "agentic-workflow-dispatch",
    "agent-registry-and-capability-discovery",
    "handoff-contract-and-state",
    "claude-subagent-delegation",
    "claude-hooks-and-guardrails",
    "workflow-evidence-and-recovery",
)
AGENTIC_GITIGNORE = (
    "# Code Workflow runtime state. Workflow records (workflows/) are committable evidence;\n"
    "# audit logs, discovery caches, and the active pointer are machine-local.\n"
    "audit/\n"
    "discovery.json\n"
    "active-workflow.json\n"
)
SKIP_DIRS = {".git", "node_modules", ".terraform", ".agentic", "dist", ".venv", "venv", "__pycache__"}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def project_dir(cli_root: str | None) -> Path:
    if cli_root:
        return Path(cli_root).resolve()
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env).resolve()
    try:
        proc = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                              capture_output=True, text=True, timeout=10)
        if proc.returncode == 0 and proc.stdout.strip():
            return Path(proc.stdout.strip()).resolve()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return Path.cwd().resolve()


def ensure_agentic_dir(root: Path) -> Path:
    """Create .agentic/ with a .gitignore so audit logs never get committed by accident."""
    agentic = root / ".agentic"
    agentic.mkdir(parents=True, exist_ok=True)
    ignore = agentic / ".gitignore"
    if not ignore.exists():
        ignore.write_text(AGENTIC_GITIGNORE, encoding="utf-8")
    return agentic


BLOCK_SCALAR_INDICATORS = (">", "|", ">-", "|-", ">+", "|+")


def frontmatter(path: Path) -> dict[str, str]:
    """Scalar key: value pairs from a markdown frontmatter block.

    Handles one-line values, plain values continued on indented lines, and > or |
    block scalars, so a description wrapped over several lines is read in full.
    Keys whose value is a list or mapping are ignored.
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}
    fields: dict[str, str] = {}
    key: str | None = None
    block: str | None = None
    parts: list[str] = []

    def flush() -> None:
        if key is None:
            return
        if block == "|":
            fields[key] = "\n".join(parts).strip()
        else:
            value = " ".join(p for p in parts if p).strip()
            fields[key] = value if block else value.strip("\"'")

    for line in match.group(1).splitlines():
        if key is not None and (line[:1] in (" ", "\t") or not line.strip()):
            parts.append(line.strip())
            continue
        flush()
        key, block, parts = None, None, []
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*?)\s*$", line)
        if not m or m.group(2).startswith("#"):
            continue
        value = m.group(2).split(" #", 1)[0].strip()
        if value in BLOCK_SCALAR_INDICATORS:
            key, block = m.group(1), value[0]
        elif value:
            key, parts = m.group(1), [value]
    flush()
    return fields


def toml_scalar(path: Path, key: str) -> str | None:
    """Top-level `key = \"value\"` from a TOML file without a TOML dependency."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = re.search(rf'^{re.escape(key)}\s*=\s*"([^"]*)"', text, re.MULTILINE)
    return m.group(1).strip() if m else None


# ---- agent-pack adapters: one scanner per ecosystem --------------------------

def _scan_claude(location: Path):
    for path in sorted(location.rglob("*.md")):
        fields = frontmatter(path)
        if fields.get("name"):
            yield fields["name"], fields.get("description", ""), path


def _scan_copilot(location: Path):
    for path in sorted(location.rglob("*.md")):
        fields = frontmatter(path)
        name = fields.get("name") or re.sub(r"\.agent$", "", path.stem)
        if fields.get("description") or fields.get("name"):
            yield name, fields.get("description", ""), path


def _scan_codex(location: Path):
    for path in sorted(location.rglob("*.toml")):
        name = toml_scalar(path, "name")
        if name:
            yield name, toml_scalar(path, "description") or "", path


ECOSYSTEMS = [
    # (client id, repo-relative dir, user-scope dir, scanner)
    ("claude-code",    ".claude/agents", ".claude/agents",  _scan_claude),
    ("github-copilot", ".github/agents", ".copilot/agents", _scan_copilot),
    ("codex",          ".codex/agents",  ".codex/agents",   _scan_codex),
]

# Maps a client ecosystem to Code Conductor's provider/harness identifiers for export.
CLIENT_IDENTITY = {
    "claude-code": ("anthropic", "claude"),
    "codex": ("openai", "codex"),
    "github-copilot": ("github", "copilot-github"),
}


def installed_agents(root: Path, include_user: bool) -> dict[str, dict]:
    """Map agent name -> {paths, description, clients} across every ecosystem."""
    found: dict[str, dict] = {}
    for client, repo_rel, user_rel, scan in ECOSYSTEMS:
        locations = [root / repo_rel]
        if include_user:
            user = Path.home() / user_rel
            if user.resolve() != locations[0].resolve():
                locations.append(user)
        for location in locations:
            if not location.is_dir():
                continue
            for name, description, path in scan(location):
                if name == ORCHESTRATOR_NAME:
                    continue
                entry = found.setdefault(name, {"paths": [], "description": "", "clients": []})
                entry["paths"].append(str(path))
                if description and not entry["description"]:
                    entry["description"] = description
                if client not in entry["clients"]:
                    entry["clients"].append(client)
    return found


def parse_registry(path: Path = REGISTRY) -> list[dict[str, str]]:
    if not path.is_file():
        raise SystemExit(
            f"agent registry not found: {path}\n"
            f"Run: python {Path(__file__).name} registry   (the registry lives beside this script)")
    items: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("- id:"):
            if current:
                items.append(current)
            current = {"id": line.split(":", 1)[1].strip()}
        elif current and ":" in line and not line.startswith("#"):
            key, value = line.split(":", 1)
            current[key.strip()] = value.strip().strip("\"'")
    if current:
        items.append(current)
    return items


CAPABILITY_LIMIT = 240


def capability_text(description: str, fallback: str, limit: int = CAPABILITY_LIMIT) -> str:
    """One-line capability summary: whitespace collapsed, quotes made YAML-safe, trimmed at a word."""
    text = " ".join((description or fallback).split()).replace('"', "'")
    if len(text) <= limit:
        return text
    cut = text[: limit + 1].rsplit(" ", 1)[0][:limit].rstrip(",;:- ")
    return cut + "..."


def write_registry(root: Path, include_user: bool) -> int:
    found = installed_agents(root, include_user)
    names = sorted(found)
    lines = [
        "# Generated by workflow.py registry -- edit capability text freely,",
        "# but agent_name must equal the installed agent's own name exactly.",
        "# clients lists which ecosystems carry this agent (claude-code, github-copilot, codex).",
        "version: 1",
        f"generated_at: {now()}",
        "agents:",
    ]
    for name in names:
        capability = capability_text(found[name]["description"], name)
        lines += [
            f"  - id: {name}",
            f"    agent_name: {name}",
            f'    capability: "{capability}"',
            f"    clients: \"{','.join(found[name]['clients'])}\"",
            "    enabled_by_default: true",
        ]
    if not names:
        lines.append("  []")
    REGISTRY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"registry written: {REGISTRY} ({len(names)} agents)")
    if not names:
        print("warning: no installed agents found in any ecosystem. Populate agent folders first.", file=sys.stderr)
    return 0


def discover(root: Path, include_user: bool) -> dict:
    found = installed_agents(root, include_user)
    registry_items = parse_registry()
    registry_names = {item["agent_name"] for item in registry_items}
    records = []
    for item in registry_items:
        entry = found.get(item["agent_name"], {"paths": [], "clients": []})
        records.append({
            "id": item["id"],
            "agent_name": item["agent_name"],
            "capability": item.get("capability", ""),
            "available": bool(entry["paths"]),
            "paths": entry["paths"],
            "clients": entry["clients"],
            "enabled_by_default": item.get("enabled_by_default", "false").lower() == "true",
        })
    unknown = sorted(n for n in found if n not in registry_names)
    return {"generated_at": now(), "root": str(root), "agents": records, "unknown_agents": unknown}


def run_discovery(root: Path, include_user: bool, out: str) -> dict:
    result = discover(root, include_user)
    ensure_agentic_dir(root)
    output = root / out
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def selected_nodes(discovery: dict, mode: str, names: list[str]) -> list[dict]:
    available = {item["id"]: item for item in discovery["agents"]}
    if mode == "all":
        requested = [item["id"] for item in discovery["agents"] if item["enabled_by_default"]]
    elif mode == "one":
        requested = names or [item["id"] for item in discovery["agents"] if item["available"]][:1]
    else:
        requested = names
    if not requested:
        raise SystemExit("no agent is available for the requested workflow mode")
    nodes = []
    for name in requested:
        if name not in available:
            nodes.append({"id": name, "agent_name": name, "required": True, "available": False,
                          "status": "blocked", "clients": []})
        else:
            item = available[name]
            nodes.append({"id": name, "agent_name": item["agent_name"], "required": True,
                          "available": item["available"], "clients": item.get("clients", []),
                          "status": "queued" if item["available"] else "blocked"})
    return nodes


def load_state(root: Path, workflow_id: str) -> tuple[Path, dict]:
    state_path = root / ".agentic" / "workflows" / workflow_id / "WORKFLOW.json"
    if not state_path.is_file():
        raise SystemExit(f"workflow not found: {workflow_id}")
    return state_path, json.loads(state_path.read_text(encoding="utf-8"))


def init_workflow(args: argparse.Namespace, root: Path) -> int:
    workflow_id = args.workflow_id or "wf-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    if not re.match(r"^[A-Za-z0-9_.-]{1,120}$", workflow_id) or workflow_id in (".", ".."):
        raise SystemExit(f"invalid workflow id: {workflow_id!r} (use letters, digits, '.', '_' or '-')")
    directory = root / ".agentic" / "workflows" / workflow_id
    if directory.exists():
        raise SystemExit(f"workflow already exists: {workflow_id}")
    discovery = run_discovery(root, include_user=not args.no_user, out=".agentic/discovery.json")
    nodes = selected_nodes(discovery, args.mode, [x for x in args.agents.split(",") if x])
    optional = {x for x in args.optional_agents.split(",") if x}
    for node in nodes:
        if args.mode == "all" and not args.require_all:
            node["required"] = bool(node["available"])
            if not node["available"]:
                node["status"] = "skipped_optional"
        if node["id"] in optional:
            node["required"] = False
            if not node["available"]:
                node["status"] = "skipped_optional"
    state = {
        "workflow_id": workflow_id,
        "tool": f"code-workflow {VERSION}",
        "created_at": now(),
        "updated_at": now(),
        "mode": args.mode,
        "objective": args.objective,
        "risk": args.risk,
        "acceptance_criteria": [x.strip() for x in args.acceptance.split(";") if x.strip()],
        "enforce_stop": bool(args.enforce_stop),
        "require_gates": bool(args.require_gates),
        "max_parallel": args.max_parallel,
        "nodes": nodes,
        "status": "blocked" if any(n["required"] and not n["available"] for n in nodes) else "queued",
    }
    (directory / "handoffs").mkdir(parents=True)
    (directory / "artifacts").mkdir()
    (directory / "evidence").mkdir()
    (directory / "WORKFLOW.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    (root / ".agentic" / "active-workflow.json").write_text(
        json.dumps({"workflow_id": workflow_id, "path": str(directory)}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(state, indent=2))
    return 0


# ---- handoff parsing (YAML subset matching the handoff contract) -------------

def _clean(value: str) -> str:
    value = value.strip()
    if " #" in value and not value.startswith(("'", '"')):
        value = value.split(" #", 1)[0].strip()
    return value.strip("\"'")


def parse_handoff(text: str) -> dict:
    """Parse the handoff contract's YAML subset: top-level scalars, lists of scalars, lists of mappings."""
    data: dict = {}
    current_key: str | None = None
    current_item: dict | None = None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if indent == 0:
            current_item = None
            m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
            if not m:
                continue
            key, value = m.group(1), m.group(2)
            if value in ("", "|", ">"):
                data[key] = []
                current_key = key
            elif value == "[]":
                data[key] = []
                current_key = None
            else:
                data[key] = _clean(value)
                current_key = None
            continue
        if current_key is None:
            continue
        if line.startswith("- "):
            body = line[2:].strip()
            m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", body)
            if m:
                current_item = {m.group(1): _clean(m.group(2))}
                data[current_key].append(current_item)
            else:
                current_item = None
                data[current_key].append(_clean(body))
        elif current_item is not None:
            m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
            if m:
                current_item[m.group(1)] = _clean(m.group(2))
    return data


def _cited_paths(data: dict) -> list[str]:
    paths = []
    for section in ("evidence", "artifacts"):
        for item in data.get(section) or []:
            if isinstance(item, dict) and item.get("path"):
                paths.append(item["path"])
    return paths


def index_paths(root: Path, paths: list[str]) -> tuple[list[dict], list[str]]:
    """Resolve cited paths inside the repository; record existence and sha256. Reject escapes."""
    records, errors = [], []
    root_resolved = root.resolve()
    for raw in paths:
        candidate = Path(raw)
        if candidate.is_absolute() or raw.startswith("~") or re.match(r"^[A-Za-z]:[\\/]", raw):
            errors.append(f"path must be repository-relative: {raw}")
            continue
        resolved = (root_resolved / candidate).resolve()
        try:
            resolved.relative_to(root_resolved)
        except ValueError:
            errors.append(f"path escapes the repository: {raw}")
            continue
        record = {"path": raw, "exists": resolved.is_file()}
        if record["exists"]:
            record["sha256"] = sha256_file(resolved)
        records.append(record)
    return records, errors


REQUIRED_HANDOFF_KEYS = ("workflow_id", "agent_id", "status", "summary", "next_action", "authorization_used")
HANDOFF_STATUSES = ("completed", "partial", "blocked", "failed_retryable", "failed_terminal")


def handoff_valid(root: Path, path: Path, node_id: str, workflow_id: str) -> tuple[bool, list[str], list[dict]]:
    if not path.is_file():
        return False, ["handoff file is missing"], []
    data = parse_handoff(path.read_text(encoding="utf-8", errors="replace"))
    errors = []
    for key in REQUIRED_HANDOFF_KEYS:
        if not isinstance(data.get(key), str) or not data.get(key):
            errors.append(f"missing {key}")
    if data.get("workflow_id") != workflow_id:
        errors.append("workflow_id does not match")
    if data.get("agent_id") != node_id:
        errors.append("agent_id does not match registered node")
    status = data.get("status")
    if isinstance(status, str) and status and status not in HANDOFF_STATUSES:
        errors.append(f"status must be one of {', '.join(HANDOFF_STATUSES)}")
    if "evidence" not in data:
        errors.append("evidence section is missing")
    index, path_errors = index_paths(root, _cited_paths(data))
    errors.extend(path_errors)
    if status == "completed" and not any(record["exists"] for record in index):
        errors.append("completed handoff cites no existing evidence or artifact file")
    return not errors, errors, index


# ---- deterministic gates ------------------------------------------------------

BUILTIN_GATE_PROFILES: dict[str, dict] = {
    "terraform": {
        "detect": {"any_suffix": [".tf"]},
        "gates": [
            {"id": "terraform-fmt", "command": ["terraform", "fmt", "-check", "-recursive"]},
            {"id": "terraform-validate", "command": ["terraform", "validate"], "requires_path": ".terraform"},
        ],
    },
    "ansible": {
        "detect": {"any_file": ["ansible.cfg", "requirements.yml", "galaxy.yml"]},
        "gates": [{"id": "ansible-lint", "command": ["ansible-lint"]}],
    },
    "node": {
        "detect": {"any_file": ["package.json"]},
        "gates": [
            {"id": "npm-typecheck", "command": ["npm", "run", "typecheck"], "requires_npm_script": "typecheck"},
            {"id": "npm-test", "command": ["npm", "test"], "requires_npm_script": "test"},
        ],
    },
    "python": {
        "detect": {"any_file": ["pyproject.toml", "pytest.ini", "setup.cfg", "tox.ini"]},
        "gates": [{"id": "pytest", "command": ["{python}", "-m", "pytest", "-q"], "requires_module": "pytest"}],
    },
}


def load_gate_profiles() -> dict[str, dict]:
    profiles = {name: dict(profile) for name, profile in BUILTIN_GATE_PROFILES.items()}
    if GATES_CONFIG.is_file():
        custom = json.loads(GATES_CONFIG.read_text(encoding="utf-8"))
        for name in custom.get("disable", []):
            profiles.pop(name, None)
        profiles.update(custom.get("profiles", {}))
    return profiles


def _repo_files(root: Path, limit: int = 20000):
    count = 0
    for _dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            yield filename
            count += 1
            if count >= limit:
                return


def detect_gate_profiles(root: Path, profiles: dict[str, dict]) -> list[str]:
    selected = []
    suffixes: set[str] | None = None
    for name, profile in profiles.items():
        detect = profile.get("detect", {})
        hit = any((root / f).exists() for f in detect.get("any_file", []))
        if not hit and detect.get("any_suffix"):
            if suffixes is None:
                suffixes = {Path(f).suffix for f in _repo_files(root)}
            hit = any(s in suffixes for s in detect["any_suffix"])
        if hit:
            selected.append(name)
    return selected


def _skip_reason(root: Path, gate: dict) -> str | None:
    if gate.get("requires_path") and not (root / gate["requires_path"]).exists():
        return f"{gate['requires_path']} not present (run the tool's init step first)"
    if gate.get("requires_npm_script"):
        try:
            scripts = json.loads((root / "package.json").read_text(encoding="utf-8")).get("scripts", {})
        except (OSError, json.JSONDecodeError):
            scripts = {}
        if gate["requires_npm_script"] not in scripts:
            return f"package.json has no '{gate['requires_npm_script']}' script"
    if gate.get("requires_module"):
        probe = subprocess.run([sys.executable, "-c", f"import {gate['requires_module']}"],
                               capture_output=True, text=True)
        if probe.returncode != 0:
            return f"python module '{gate['requires_module']}' is not installed"
    return None


def run_gates(args: argparse.Namespace, root: Path) -> int:
    state_path, state = load_state(root, args.workflow)
    profiles = load_gate_profiles()
    selected = [p for p in args.profiles.split(",") if p] or detect_gate_profiles(root, profiles)
    evidence_dir = state_path.parent / "evidence"
    evidence_dir.mkdir(exist_ok=True)
    results = []
    for profile_name in selected:
        profile = profiles.get(profile_name)
        if not profile:
            raise SystemExit(f"unknown gate profile: {profile_name}")
        for gate in profile.get("gates", []):
            command = [sys.executable if part == "{python}" else part for part in gate["command"]]
            record = {"gate": gate["id"], "profile": profile_name, "blocking": gate.get("blocking", True),
                      "command": " ".join(command)}
            reason = _skip_reason(root, gate)
            resolved = shutil.which(command[0]) if reason is None else None
            if reason is None and resolved is None:
                reason = f"'{command[0]}' is not installed"
            if reason:
                record.update(status="skipped", summary=f"skipped: {reason}")
            else:
                try:
                    proc = subprocess.run([resolved] + command[1:], cwd=root, capture_output=True, text=True,
                                          timeout=int(gate.get("timeout_seconds", 600)))
                    output, code, timed_out = (proc.stdout or "") + (proc.stderr or ""), proc.returncode, False
                except subprocess.TimeoutExpired as exc:
                    output, code, timed_out = str(exc.stdout or "") + str(exc.stderr or ""), None, True
                log = evidence_dir / f"gate-{gate['id']}.log"
                log.write_text(f"$ {record['command']}\n{output}", encoding="utf-8")
                passed = code == 0 and not timed_out
                record.update(status="passed" if passed else "failed",
                              summary=("passed" if passed else ("timed out" if timed_out else f"failed (exit {code})")),
                              evidence_path=str(log.relative_to(root)).replace("\\", "/"),
                              sha256=sha256_file(log))
            results.append(record)
    state["gates"] = {"ran_at": now(), "profiles": selected, "results": results}
    state["updated_at"] = now()
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(state["gates"], indent=2))
    failed = [r for r in results if r["blocking"] and r["status"] == "failed"]
    return 1 if failed else 0


def gate_errors(state: dict) -> list[str]:
    gates = state.get("gates")
    errors = []
    if gates:
        errors += [f"gate failed: {r['gate']} ({r['summary']})" for r in gates["results"]
                   if r.get("blocking", True) and r["status"] == "failed"]
    if state.get("require_gates"):
        if not gates:
            errors.append("workflow requires gates but none have been run (workflow.py gates --workflow <id>)")
        else:
            errors += [f"required gate not run: {r['gate']} ({r['summary']})" for r in gates["results"]
                       if r.get("blocking", True) and r["status"] == "skipped"]
            if not gates["results"]:
                errors.append("workflow requires gates but no gate profile matched this repository")
    return errors


def validate_workflow(args: argparse.Namespace, root: Path) -> int:
    state_path, state = load_state(root, args.workflow)
    directory = state_path.parent
    errors: list[str] = []
    results = []
    for node in state.get("nodes", []):
        handoff = directory / "handoffs" / f"{node['id']}.yml"
        if not node.get("available"):
            if node.get("required"):
                errors.append(f"required agent unavailable: {node['id']}")
                node["status"] = "blocked"
            else:
                node["status"] = "skipped_optional"
            results.append({"agent_id": node["id"], "valid": False, "reasons": [node["status"]]})
            continue
        valid, reasons, index = handoff_valid(root, handoff, node["id"], state["workflow_id"])
        if valid:
            node["status"] = "completed"
        else:
            node["status"] = "blocked" if node.get("required") else "partial"
            if node.get("required"):
                errors.extend(f"{node['id']}: {reason}" for reason in reasons)
        results.append({"agent_id": node["id"], "valid": valid, "reasons": reasons, "evidence_index": index})
    errors.extend(gate_errors(state))
    required = [node for node in state.get("nodes", []) if node.get("required")]
    if errors:
        state["status"] = "blocked"
    elif required and all(node.get("status") == "completed" for node in required):
        state["status"] = "completed"
    else:
        state["status"] = "partial"
    state["updated_at"] = now()
    state["validation"] = {"validated_at": now(), "errors": errors, "results": results}
    if not args.check:
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(state["validation"], workflow_status=state["status"]), indent=2))
    return 0 if not errors else 1


# ---- export: Code Conductor RunManifest-compatible projection -----------------

SEVERITIES = ("info", "low", "medium", "high", "critical")
EXPORT_STATUS = {
    "completed": ("completed", "review"),
    "partial": ("completed", "review"),
    "blocked": ("blocked", "human_required"),
    "failed_retryable": ("failed", "changes_required"),
    "failed_terminal": ("failed", "changes_required"),
}


def export_workflow(args: argparse.Namespace, root: Path) -> int:
    """Project the workflow into Code Conductor's RunManifest shape (shared contract, ADR 0011).

    Boundary: Code Workflow never recommends `ready` and never writes `mergeDecision`;
    readiness belongs to Code Conductor's independent review and gates.
    """
    state_path, state = load_state(root, args.workflow)
    directory = state_path.parent
    workflow_id = state["workflow_id"]
    risk = state.get("risk", "R1")
    task = {
        "id": workflow_id,
        "objective": state.get("objective", ""),
        "repository": str(root),
        "acceptanceCriteria": state.get("acceptance_criteria", []),
        "risk": risk if risk in RISK_CLASSES else "R1",
        "constraints": ["Executed by Code Workflow inside one client: no cross-provider independence, "
                        "worktree isolation, or merge-readiness review was applied."],
        "createdAt": state.get("created_at", now()),
    }
    assignments, results = [], []
    for node in state.get("nodes", []):
        if node.get("status") == "skipped_optional" or (not node.get("available") and not node.get("required")):
            task["constraints"].append(f"skipped_optional: {node['id']}")
            continue
        handoff_path = directory / "handoffs" / f"{node['id']}.yml"
        data = parse_handoff(handoff_path.read_text(encoding="utf-8", errors="replace")) if handoff_path.is_file() else {}
        clients = node.get("clients") or []
        provider, harness = CLIENT_IDENTITY.get(clients[0], ("unknown", "code-workflow")) if clients else ("unknown", "code-workflow")
        provider = data.get("provider") or provider
        harness = data.get("harness") or harness
        assignment_id = f"{workflow_id}:{node['id']}"
        authorization = str(data.get("authorization_used", "")).lower()
        assignments.append({
            "id": assignment_id, "taskId": workflow_id, "agentId": node["agent_name"], "role": "specialist",
            "stance": "neutral", "provider": provider, "harness": harness, "billingChannel": "subscription",
            "authority": ["observe", "recommend"] if "read" in authorization else ["recommend"], "dependsOn": [],
        })
        index, _ = index_paths(root, _cited_paths(data))
        hashes = {record["path"]: record.get("sha256") for record in index}
        cited = [i for i in (data.get("evidence") or []) + (data.get("artifacts") or []) if isinstance(i, dict) and i.get("path")]
        evidence = []
        for n, item in enumerate(cited, 1):
            record = {"id": f"E-{node['id']}-{n}", "kind": "repository", "source": item["path"],
                      "summary": item.get("detail") or item.get("kind") or item["path"], "uri": item["path"]}
            if hashes.get(item["path"]):
                record["sha256"] = hashes[item["path"]]
            evidence.append(record)
        findings, risks = [], []
        for n, risk_item in enumerate([r for r in data.get("risks") or [] if isinstance(r, dict)], 1):
            severity = str(risk_item.get("severity", "medium")).lower()
            severity = severity if severity in SEVERITIES else "medium"
            detail = risk_item.get("detail") or risk_item.get("id") or "unspecified risk"
            findings.append({"id": risk_item.get("id") or f"F-{node['id']}-{n}", "severity": severity,
                             "summary": detail, "evidenceIds": [], "blocking": severity in ("high", "critical")})
            risks.append(detail)
        if not handoff_path.is_file():
            status, recommendation, blockers = "blocked", "human_required", ["handoff file is missing"]
        elif not node.get("available"):
            status, recommendation, blockers = "blocked", "human_required", ["required agent unavailable"]
        else:
            status, recommendation = EXPORT_STATUS.get(data.get("status", ""), ("failed", "changes_required"))
            blockers = [data["next_action"]] if status == "blocked" and data.get("next_action") else []
        result = {
            "taskId": workflow_id, "assignmentId": assignment_id, "agentId": node["agent_name"], "role": "specialist",
            "stance": "neutral", "provider": provider, "harness": harness, "billingChannel": "subscription",
            "status": status,
            "changes": [i["path"] for i in data.get("artifacts") or []
                        if isinstance(i, dict) and i.get("kind") == "source" and i.get("path")],
            "tests": [], "evidence": evidence, "findings": findings, "risks": risks, "blockers": blockers,
            "recommendation": recommendation,
        }
        not_verified = [v for v in data.get("not_verified") or [] if isinstance(v, str) and v]
        if not_verified:
            result["notVerified"] = not_verified
        results.append(result)
    gates = [{"gate": r["gate"], "status": r["status"], "evidenceIds": [],
              "summary": r["summary"] + (f" (log {r['evidence_path']} sha256 {r['sha256']})" if r.get("sha256") else "")}
             for r in (state.get("gates") or {}).get("results", [])]
    manifest = {"runId": workflow_id, "task": task, "assignments": assignments, "results": results, "gates": gates}
    target = directory / "run-manifest.json"
    target.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(str(target))
    return 0


# ---- doctor -------------------------------------------------------------------

def _has_orchestrator(dirs, scanner) -> bool:
    for directory in dirs:
        if directory.is_dir():
            for name, _description, _path in scanner(directory):
                if name == ORCHESTRATOR_NAME:
                    return True
    return False


def doctor(args: argparse.Namespace, root: Path) -> int:
    lines: list[tuple[str, str]] = []

    def add(level: str, text: str) -> None:
        lines.append((level, text))

    add("OK" if sys.version_info >= (3, 8) else "ERROR", f"python {sys.version.split()[0]} (requires 3.8+)")
    add("OK", f"code-workflow {VERSION}; repository root: {root}")
    for rel in ("tooling/workflow.py", "hooks/claude_event.py"):
        add("OK" if (root / rel).is_file() else "ERROR", f"repo file {rel}")
    home = Path.home()
    clients = {
        "claude-code": _has_orchestrator((home / ".claude/agents", root / ".claude/agents"), _scan_claude),
        "codex": _has_orchestrator((home / ".codex/agents", root / ".codex/agents"), _scan_codex),
        "github-copilot": _has_orchestrator((home / ".copilot/agents", root / ".github/agents"), _scan_copilot),
    }
    for client, present in clients.items():
        add("OK" if present else "INFO", f"orchestrator agent for {client}: {'installed' if present else 'not installed'}")
    if not any(clients.values()):
        add("ERROR", "the orchestrator agent is not installed for any client (run install.ps1 / install.sh)")
    for label, base in (("~/.claude/skills", home / ".claude/skills"), ("~/.agents/skills", home / ".agents/skills")):
        missing = [s for s in EXPECTED_SKILLS if not (base / s / "SKILL.md").is_file()]
        if base.is_dir() and not missing:
            add("OK", f"all {len(EXPECTED_SKILLS)} skills in {label}")
        elif base.is_dir():
            add("WARN", f"{label} missing skills: {', '.join(missing)}")
        else:
            add("INFO", f"{label} not present")
    settings = root / ".claude" / "settings.json"
    merged = settings.is_file() and "claude_event.py" in settings.read_text(encoding="utf-8", errors="replace")
    add("OK" if merged else "INFO",
        "Claude hook entries merged into .claude/settings.json" if merged
        else "Claude hook entries not merged into .claude/settings.json (optional audit hooks; run the installer)")
    codex_hooks = (root / ".codex" / "hooks.json").is_file()
    add("OK" if codex_hooks else "INFO",
        ".codex/hooks.json present (Codex runs it only after you trust it via /hooks)" if codex_hooks
        else ".codex/hooks.json not active (optional: rename .codex/hooks.sample.json to hooks.json "
             "after review, then trust it via /hooks)")
    agents_md = root / "AGENTS.md"
    has_section = agents_md.is_file() and "BEGIN claude-agentic-orchestrator" in agents_md.read_text(encoding="utf-8", errors="replace")
    add("OK" if has_section else "INFO",
        "AGENTS.md has the orchestration section (used by Codex and Copilot)" if has_section
        else "AGENTS.md has no orchestration section (needed only for Codex and Copilot)")
    if REGISTRY.is_file():
        registered = {item["agent_name"] for item in parse_registry()}
        installed = set(installed_agents(root, include_user=True))
        stale, new = sorted(registered - installed), sorted(installed - registered)
        if stale or new:
            add("WARN", f"registry out of date (not installed: {stale or 'none'}; unregistered: {new or 'none'}) -> run: workflow.py registry")
        else:
            add("OK", f"registry matches {len(registered)} installed agent(s)")
    else:
        add("ERROR", "tooling/agent-registry.yml missing -> run: workflow.py registry")
    agentic = root / ".agentic"
    add("OK" if (agentic / ".gitignore").is_file() or not agentic.exists() else "WARN",
        ".agentic/.gitignore keeps audit logs out of git")
    for level, text in lines:
        print(f"{level:5} {text}")
    return 1 if any(level == "ERROR" for level, _ in lines) else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", action="version", version=f"code-workflow {VERSION}")
    parser.add_argument("--root", default=None,
                        help="repository root (default: CLAUDE_PROJECT_DIR, then git toplevel, then cwd)")
    sub = parser.add_subparsers(dest="command", required=True)
    registry_parser = sub.add_parser("registry", help="regenerate agent-registry.yml from installed agents (all ecosystems)")
    registry_parser.add_argument("--no-user", action="store_true")
    discover_parser = sub.add_parser("discover")
    discover_parser.add_argument("--out", default=".agentic/discovery.json")
    discover_parser.add_argument("--no-user", action="store_true")
    init_parser = sub.add_parser("init")
    init_parser.add_argument("--mode", choices=["one", "selected", "all"], required=True)
    init_parser.add_argument("--agents", default="")
    init_parser.add_argument("--optional-agents", default="")
    init_parser.add_argument("--workflow-id")
    init_parser.add_argument("--objective", required=True)
    init_parser.add_argument("--acceptance", default="", help="acceptance criteria, separated by ';'")
    init_parser.add_argument("--risk", choices=list(RISK_CLASSES), default="R1",
                             help="risk class carried into export (informational in Code Workflow)")
    init_parser.add_argument("--max-parallel", type=int, default=3)
    init_parser.add_argument("--require-all", action="store_true")
    init_parser.add_argument("--require-gates", action="store_true",
                             help="validation fails unless every detected blocking gate passed")
    init_parser.add_argument("--enforce-stop", action="store_true")
    init_parser.add_argument("--no-user", action="store_true")
    gates_parser = sub.add_parser("gates", help="run deterministic repository checks and record evidence")
    gates_parser.add_argument("--workflow", required=True)
    gates_parser.add_argument("--profiles", default="", help="comma-separated profiles (default: auto-detect)")
    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("--workflow", required=True)
    validate_parser.add_argument("--check", action="store_true", help="read-only: report without rewriting WORKFLOW.json")
    export_parser = sub.add_parser("export", help="write a Code Conductor RunManifest-compatible run-manifest.json")
    export_parser.add_argument("--workflow", required=True)
    sub.add_parser("doctor", help="check installation health")
    status_parser = sub.add_parser("status")
    status_parser.add_argument("--workflow", required=True)
    args = parser.parse_args()
    root = project_dir(args.root)
    if args.command == "registry":
        return write_registry(root, include_user=not args.no_user)
    if args.command == "discover":
        print(json.dumps(run_discovery(root, include_user=not args.no_user, out=args.out), indent=2))
        return 0
    if args.command == "init":
        return init_workflow(args, root)
    if args.command == "gates":
        return run_gates(args, root)
    if args.command == "validate":
        return validate_workflow(args, root)
    if args.command == "export":
        return export_workflow(args, root)
    if args.command == "doctor":
        return doctor(args, root)
    state_path, _ = load_state(root, args.workflow)
    print(state_path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
