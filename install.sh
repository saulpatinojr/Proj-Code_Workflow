#!/usr/bin/env bash
# Claude Agentic Orchestrator - interactive installer (macOS / Linux)
# Clients: Claude Code, OpenAI Codex CLI, GitHub Copilot (pick any combination).
# Safe to re-run: identical files skip, hook merge and AGENTS.md append are idempotent.
set -eo pipefail  # no -u: macOS ships bash 3.2, where empty-array expansion trips nounset

CYAN=$'\033[36m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; RED=$'\033[31m'; GRAY=$'\033[90m'; NC=$'\033[0m'
step()  { printf '\n%s==> %s%s\n' "$CYAN" "$1" "$NC"; }
ok()    { printf '    %s[OK]%s %s\n' "$GREEN" "$NC" "$1"; }
warn()  { printf '    %s[!]%s %s\n'  "$YELLOW" "$NC" "$1"; }
fail()  { printf '    %s[X]%s %s\n'  "$RED" "$NC" "$1"; }
note()  { printf '    %s%s%s\n' "$GRAY" "$1" "$NC"; }

confirm() { # confirm "question" default(y/n)
  local q="$1" d="${2:-y}" a suffix
  if [ "$d" = y ]; then suffix='[Y/n]'; else suffix='[y/N]'; fi
  read -r -p "$q $suffix: " a || a=''
  a="$(printf '%s' "$a" | tr '[:upper:]' '[:lower:]')"
  if [ -z "$a" ]; then [ "$d" = y ]; else case "$a" in y*) true;; *) false;; esac; fi
}

hash_of() { if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | cut -d' ' -f1; else sha256sum "$1" | cut -d' ' -f1; fi }

copy_tree() { # copy_tree SRC DST
  local src="$1" dst="$2" copied=0 skipped=0 rel target
  while IFS= read -r -d '' f; do
    rel="${f#"$src"/}"; target="$dst/$rel"
    mkdir -p "$(dirname "$target")"
    if [ -f "$target" ]; then
      if [ "$(hash_of "$f")" = "$(hash_of "$target")" ]; then skipped=$((skipped+1)); continue; fi
      if ! confirm "    Overwrite existing (differs): $rel" n; then skipped=$((skipped+1)); continue; fi
    fi
    cp "$f" "$target"; copied=$((copied+1))
  done < <(find "$src" -type f -print0)
  ok "$copied file(s) copied, $skipped skipped (identical or kept)"
}

printf '\n%s=============================================================%s\n' "$CYAN" "$NC"
printf '%s  Claude Agentic Orchestrator - interactive installer%s\n' "$CYAN" "$NC"
printf '%s=============================================================%s\n' "$CYAN" "$NC"
printf '  Read PLACEMENT.md for the full map of what goes where.\n'

# ---------------------------------------------------------------- python
PY=''
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info[0]==3 else 1)' 2>/dev/null; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then fail 'Python 3 is required (macOS: xcode-select --install, or brew install python).'; exit 1; fi

# ---------------------------------------------------------------- step 1: payloads
step 'Step 1/7  Locating the pack payloads'
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PACK_ROOT=''
for c in "$SCRIPT_DIR" "$SCRIPT_DIR"/* "$SCRIPT_DIR"/*/* "$(dirname "$SCRIPT_DIR")" "$(dirname "$SCRIPT_DIR")"/*; do
  [ -d "$c/user-claude" ] && [ -d "$c/repo-root" ] && { PACK_ROOT="$c"; break; }
done
VERIFY_MODE=0
if [ -n "$PACK_ROOT" ]; then
  ok "Pack payloads found at: $PACK_ROOT"
else
  VERIFY_MODE=1
  warn 'Payload folders (user-claude/ + repo-root/) not found near this script.'
  ok  'Switching to VERIFY MODE: assuming you already copied the files manually.'
fi

# ---------------------------------------------------------------- step 2: client selection
step 'Step 2/7  Selecting clients'
note 'Detected on this machine:'
CLA=n; COD=n; COP=n
[ -d "$HOME/.claude" ]  && note '  - Claude Code   (~/.claude exists)'
[ -d "$HOME/.codex" ]   && note '  - Codex CLI     (~/.codex exists)'
[ -d "$HOME/.copilot" ] && note '  - Copilot CLI   (~/.copilot exists)'
confirm '    Install for Claude Code?' y  && CLA=y
confirm '    Install for OpenAI Codex CLI?' "$([ -d "$HOME/.codex" ] && echo y || echo n)" && COD=y
confirm '    Install for GitHub Copilot?' "$([ -d "$HOME/.copilot" ] && echo y || echo n)" && COP=y
[ "$CLA$COD$COP" = "nnn" ] && { fail 'No client selected.'; exit 0; }

# ---------------------------------------------------------------- step 3: user-scope installs
step 'Step 3/7  User-scope agent + skills'
SK_SRC=''
[ -n "$PACK_ROOT" ] && SK_SRC="$PACK_ROOT/user-claude/skills"

if [ "$CLA" = y ]; then
  mkdir -p "$HOME/.claude"
  if [ "$VERIFY_MODE" = 1 ]; then
    if grep -rqs '^name: claude-agentic-orchestrator' "$HOME/.claude/agents" 2>/dev/null; then ok 'Claude: orchestrator agent present'; else warn 'Claude: orchestrator agent NOT found in ~/.claude/agents'; fi
  else
    note "Claude Code -> ~/.claude"
    copy_tree "$PACK_ROOT/user-claude" "$HOME/.claude"
  fi
fi
if [ "$COD" = y ]; then
  mkdir -p "$HOME/.codex/agents" "$HOME/.agents/skills"
  if [ "$VERIFY_MODE" = 1 ]; then
    [ -f "$HOME/.codex/agents/claude-agentic-orchestrator.toml" ] && ok 'Codex: orchestrator agent present' || warn 'Codex: ~/.codex/agents/claude-agentic-orchestrator.toml missing'
  else
    note "Codex -> ~/.codex/agents (agent) + ~/.agents/skills (skills, shared standard)"
    copy_tree "$PACK_ROOT/user-codex/agents" "$HOME/.codex/agents"
    copy_tree "$SK_SRC" "$HOME/.agents/skills"
  fi
fi
if [ "$COP" = y ]; then
  mkdir -p "$HOME/.copilot/agents" "$HOME/.agents/skills"
  if [ "$VERIFY_MODE" = 1 ]; then
    [ -f "$HOME/.copilot/agents/claude-agentic-orchestrator.agent.md" ] && ok 'Copilot: orchestrator agent present' || warn 'Copilot: ~/.copilot/agents/claude-agentic-orchestrator.agent.md missing'
  else
    note "Copilot -> ~/.copilot/agents (agent) + ~/.agents/skills (skills, shared standard)"
    copy_tree "$PACK_ROOT/user-copilot/agents" "$HOME/.copilot/agents"
    [ "$COD" = y ] || copy_tree "$SK_SRC" "$HOME/.agents/skills"
  fi
fi

# ---------------------------------------------------------------- step 4: repository
step 'Step 4/7  Repository tooling and hooks'
REPO="${1:-}"
while [ -z "$REPO" ] || [ ! -d "$REPO" ]; do
  [ -n "$REPO" ] && warn "Not a folder: $REPO"
  read -r -p '    Path to the repository where workflows will run: ' REPO
  REPO="${REPO/#\~/$HOME}"
done
REPO="$(cd "$REPO" && pwd)"
ok "Target repository: $REPO"
if [ "$VERIFY_MODE" = 1 ]; then
  for rel in hooks/claude_event.py tooling/workflow.py tooling/agent-registry.yml; do
    [ -f "$REPO/$rel" ] && ok "present: $rel" || warn "MISSING: $rel (copy from repo-root/)"
  done
else
  copy_tree "$PACK_ROOT/repo-root/hooks" "$REPO/hooks"
  copy_tree "$PACK_ROOT/repo-root/tooling" "$REPO/tooling"
  if [ "$COD" = y ]; then mkdir -p "$REPO/.codex"; copy_tree "$PACK_ROOT/repo-root/.codex" "$REPO/.codex"; fi
  if [ "$COP" = y ]; then mkdir -p "$REPO/.github/hooks"; copy_tree "$PACK_ROOT/repo-root/.github" "$REPO/.github"; fi
fi

# ---------------------------------------------------------------- step 5: hook settings merge
step "Step 5/7  Merging Claude hook entries into $REPO/.claude/settings.json"
if [ "$CLA" = y ] || [ "$COP" = y ]; then
  mkdir -p "$REPO/.claude"
  "$PY" - "$REPO/.claude/settings.json" << 'PYMERGE'
import json, shutil, sys
from pathlib import Path
path = Path(sys.argv[1])
hook = lambda ev: {"hooks": [{"type": "command",
    "command": 'python3 "${CLAUDE_PROJECT_DIR}/hooks/claude_event.py" --event ' + ev}]}
pack = {ev: [hook(ev)] for ev in ["SessionStart", "SubagentStart", "SubagentStop"]}
pack["Stop"] = [{"hooks": [{"type": "command",
    "command": 'python3 "${CLAUDE_PROJECT_DIR}/hooks/claude_event.py" --event Stop', "timeout": 30}]}]
if path.is_file():
    shutil.copy(path, str(path) + ".backup-orchestrator")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
else:
    data = {}
hooks = data.setdefault("hooks", {})
added = present = 0
for ev, entries in pack.items():
    existing = hooks.setdefault(ev, [])
    if "claude_event.py" in json.dumps(existing):
        present += 1
        continue
    existing.extend(entries)
    added += 1
path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print(f"    [OK] {added} hook event(s) merged, {present} already present. Existing settings preserved.")
PYMERGE
  [ "$COP" = y ] && warn 'VS Code Copilot reads these Claude hooks only when chat.useClaudeHooks is enabled (off by default).'
else
  note 'Skipped (Codex only; Codex uses .codex/hooks.sample.json instead).'
fi

# ---------------------------------------------------------------- step 6: AGENTS.md section
step "Step 6/7  AGENTS.md orchestration section"
if [ "$COD" = y ] || [ "$COP" = y ]; then
  AG="$REPO/AGENTS.md"
  SRC_BLOCK=''
  if [ -n "$PACK_ROOT" ] && [ -f "$PACK_ROOT/repo-root/AGENTS-orchestrator.md" ]; then SRC_BLOCK="$PACK_ROOT/repo-root/AGENTS-orchestrator.md";
  elif [ -f "$REPO/AGENTS-orchestrator.md" ]; then SRC_BLOCK="$REPO/AGENTS-orchestrator.md"; fi
  if [ -z "$SRC_BLOCK" ]; then
    warn 'AGENTS-orchestrator.md not found; skipping AGENTS.md update.'
  elif [ -f "$AG" ] && grep -q 'BEGIN claude-agentic-orchestrator' "$AG"; then
    ok 'AGENTS.md already contains the orchestration section.'
  else
    { [ -f "$AG" ] && printf '\n'; cat "$SRC_BLOCK"; } >> "$AG"
    ok "Orchestration section appended to $AG"
  fi
else
  note 'Skipped (only Claude selected; Claude uses the agent + skills directly).'
fi

# ---------------------------------------------------------------- step 7: guided tooling run
step 'Step 7/7  Running the Python workflow tooling (guided)'
ok "Using: $PY"
if [ ! -f "$REPO/tooling/workflow.py" ]; then
  warn 'tooling/workflow.py is not in the repository; skipping the guided run.'
  exit 0
fi
cd "$REPO"
note 'The registry is generated from your INSTALLED agents (all ecosystems, repo + user scope).'
confirm '    Run now: workflow.py registry ?' y && "$PY" tooling/workflow.py registry
note 'Discover reports which registry agents are installed, where, and for which clients.'
confirm '    Run now: workflow.py discover ?' y && "$PY" tooling/workflow.py discover
note 'A workflow records delegation state under .agentic/ before any agent runs.'
if confirm '    Create a workflow now (workflow.py init)?' n; then
  MODE=''
  while [ "$MODE" != one ] && [ "$MODE" != selected ] && [ "$MODE" != all ]; do
    read -r -p '      Mode  [one | selected | all]: ' MODE; MODE="$(printf '%s' "$MODE" | tr '[:upper:]' '[:lower:]')"
  done
  AGENTS_ARG=()
  if [ "$MODE" = selected ] || [ "$MODE" = one ]; then
    IDS=()
    while IFS= read -r line; do IDS[${#IDS[@]}]="$line"; done < <("$PY" - << 'PYIDS' 2>/dev/null
import json, pathlib
d = json.loads(pathlib.Path(".agentic/discovery.json").read_text())
for a in d["agents"]:
    print(f"{a['id']}\t{'yes' if a['available'] else 'NO'}")
PYIDS
)
    if [ "${#IDS[@]}" -gt 0 ]; then
      printf '\n      %-4s %-40s %s\n' '#' 'Agent id' 'Installed'
      i=1
      for row in "${IDS[@]}"; do
        printf '      %-4s %-40s %s\n' "$i" "${row%%$'\t'*}" "${row##*$'\t'}"; i=$((i+1))
      done
      SEL=''
      while [ -z "$SEL" ]; do
        read -r -p "      Pick numbers, e.g. 1,4,6 or 2-5 (or 'a' for all installed): " RAW
        SEL="$("$PY" - "$RAW" "${IDS[@]}" << 'PYPICK'
import sys
raw, rows = sys.argv[1].strip().lower(), sys.argv[2:]
ids = [r.split("\t")[0] for r in rows]; avail = [r.split("\t")[1] == "yes" for r in rows]
out = []
try:
    if raw == "a":
        out = [i for i, okx in zip(ids, avail) if okx]
    else:
        for tok in raw.replace(",", " ").split():
            if "-" in tok:
                lo, hi = map(int, tok.split("-", 1)); out += ids[lo-1:hi]
            else:
                out.append(ids[int(tok)-1])
    seen = []
    [seen.append(x) for x in out if x not in seen]
    print(",".join(seen))
except Exception:
    print("")
PYPICK
)"
        [ -z "$SEL" ] && warn "Invalid selection: $RAW"
      done
      ok "Selected: $SEL"
      AGENTS_ARG=(--agents "$SEL")
    else
      read -r -p '      Agent ids, comma-separated: ' SEL
      AGENTS_ARG=(--agents "$SEL")
    fi
  fi
  OBJ=''
  while [ -z "$OBJ" ]; do read -r -p '      Objective (one line): ' OBJ; done
  ENF=()
  confirm '      Enforce completion at session stop (--enforce-stop)?' n && ENF=(--enforce-stop)
  "$PY" tooling/workflow.py init --mode "$MODE" ${AGENTS_ARG[@]+"${AGENTS_ARG[@]}"} --objective "$OBJ" ${ENF[@]+"${ENF[@]}"}
  note 'Validate later with: '"$PY"' tooling/workflow.py validate --workflow <workflow-id>'
fi

printf '\n%s=============================================================%s\n' "$GREEN" "$NC"
printf '%s  Install complete.%s\n' "$GREEN" "$NC"
[ "$CLA" = y ] && printf '%s  Claude Code : new session from %s, then @agent-claude-agentic-orchestrator or claude --agent claude-agentic-orchestrator%s\n' "$GREEN" "$REPO" "$NC"
[ "$COD" = y ] && printf '%s  Codex CLI   : codex, then ask for the orchestrator; enable .codex/hooks.sample.json after review + trust via /hooks%s\n' "$GREEN" "$NC"
[ "$COP" = y ] && printf '%s  Copilot     : copilot --agent claude-agentic-orchestrator (CLI) or pick the agent in VS Code chat; enable .github/hooks/*.sample.json after review%s\n' "$GREEN" "$NC"
printf '%s=============================================================%s\n' "$GREEN" "$NC"
