"""Code Workflow regression suite (stdlib unittest; runs on Windows, macOS, and Linux)."""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "repo-root"
SCHEMA = json.loads((ROOT / "tests" / "fixtures" / "code-conductor-contracts.schema.json").read_text(encoding="utf-8"))
EXPECTED_SKILLS = [
    "agentic-workflow-dispatch",
    "agent-registry-and-capability-discovery",
    "handoff-contract-and-state",
    "claude-subagent-delegation",
    "claude-hooks-and-guardrails",
    "workflow-evidence-and-recovery",
]


# ---- minimal JSON Schema validator for the subset the contract uses ----------

def schema_errors(value, schema, path="$"):
    if "$ref" in schema:
        name = schema["$ref"].split("/")[-1]
        return schema_errors(value, SCHEMA["$defs"][name], path)
    errors = []
    expected = schema.get("type")
    checks = {"object": dict, "array": list, "string": str, "boolean": bool}
    if expected in checks and not isinstance(value, checks[expected]):
        return [f"{path}: expected {expected}"]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} not in enum")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: shorter than minLength")
        if schema.get("format") == "date-time" and not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", value):
            errors.append(f"{path}: not date-time")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing {key}")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            errors += [f"{path}: unexpected {key}" for key in value if key not in props]
        for key, sub in props.items():
            if key in value:
                errors += schema_errors(value[key], sub, f"{path}.{key}")
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            errors += schema_errors(item, schema["items"], f"{path}[{i}]")
    return errors


# ---- sandbox helpers ----------------------------------------------------------

class Sandbox:
    """A fake repository + fake home, with the tooling and hooks copied in."""

    def __init__(self):
        self.base = Path(tempfile.mkdtemp(prefix="cw-test-"))
        self.repo = self.base / "repo"
        self.home = self.base / "home"
        self.repo.mkdir()
        self.home.mkdir()
        shutil.copytree(PAYLOAD / "tooling", self.repo / "tooling")
        shutil.copytree(PAYLOAD / "hooks", self.repo / "hooks")

    def env(self):
        env = dict(os.environ)
        env["HOME"] = str(self.home)
        env["USERPROFILE"] = str(self.home)
        env.pop("CLAUDE_PROJECT_DIR", None)
        return env

    def write(self, rel, text, base=None):
        path = (base or self.repo) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def wf(self, *args, check=True):
        proc = subprocess.run([sys.executable, str(self.repo / "tooling" / "workflow.py"), "--root", str(self.repo), *args],
                              cwd=self.repo, env=self.env(), capture_output=True, text=True)
        if check and proc.returncode not in (0, 1):
            raise AssertionError(f"workflow.py {args} crashed:\n{proc.stdout}\n{proc.stderr}")
        return proc

    def hook(self, payload, *args):
        return subprocess.run([sys.executable, str(self.repo / "hooks" / "claude_event.py"), *args],
                              input=json.dumps(payload), cwd=self.repo, env=self.env(), capture_output=True, text=True)

    def handoff(self, workflow_id, agent_id, status="completed", evidence_path="main.tf", extra=""):
        text = (
            f"workflow_id: {workflow_id}\nagent_id: {agent_id}\nagent_name: {agent_id}\nstatus: {status}\n"
            "summary: Reviewed the change.\nevidence:\n"
            f"  - path: {evidence_path}\n    detail: Reviewed configuration.\n"
            "artifacts: []\nrisks:\n  - id: RISK-001\n    severity: high\n    detail: State backend not encrypted.\n"
            "next_action: none\nauthorization_used: read-only\nnot_verified:\n  - Live deployment was not performed.\n"
            + extra
        )
        return self.write(f".agentic/workflows/{workflow_id}/handoffs/{agent_id}.yml", text)

    def cleanup(self):
        def unlock_and_retry(func, path, *_):
            # git writes its object files read-only, which shutil.rmtree cannot delete on Windows
            os.chmod(path, stat.S_IWRITE)
            func(path)
        if sys.version_info >= (3, 12):
            shutil.rmtree(self.base, onexc=unlock_and_retry)
        else:
            shutil.rmtree(self.base, onerror=unlock_and_retry)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.sb = Sandbox()
        sb = self.sb
        sb.write(".claude/agents/azure.md", "---\nname: azure-architect\ndescription: Azure specialist\n---\nbody\n")
        sb.write(".github/agents/pr-reviewer.agent.md", "---\nname: pr-reviewer\ndescription: Reviews PRs\n---\nbody\n")
        sb.write(".claude/agents/tf.md", "---\nname: terraform-expert-engineer\ndescription: Terraform\n---\n", base=sb.home)
        sb.write(".codex/agents/cost.toml", 'name = "cost-analyzer"\ndescription = "FinOps"\ndeveloper_instructions = """x"""\n', base=sb.home)
        sb.write(".copilot/agents/azure-architect.agent.md", "---\nname: azure-architect\ndescription: dup\n---\n", base=sb.home)
        sb.write(".claude/agents/orch.md", "---\nname: claude-agentic-orchestrator\ndescription: self\n---\n", base=sb.home)
        sb.write("main.tf", "terraform {}\n")
        self.assertEqual(sb.wf("registry").returncode, 0)

    def tearDown(self):
        self.sb.cleanup()

    def test_registry_merges_ecosystems_and_excludes_orchestrator(self):
        discovery = json.loads(self.sb.wf("discover").stdout)
        agents = {a["id"]: a for a in discovery["agents"]}
        self.assertEqual(set(agents), {"azure-architect", "pr-reviewer", "terraform-expert-engineer", "cost-analyzer"})
        self.assertEqual(sorted(agents["azure-architect"]["clients"]), ["claude-code", "github-copilot"])
        self.assertEqual(agents["cost-analyzer"]["clients"], ["codex"])

    def test_client_filter_counts_only_agents_that_client_can_run(self):
        sb = self.sb
        discovery = json.loads(sb.wf("discover", "--client", "claude-code").stdout)
        available = {a["id"]: a["available"] for a in discovery["agents"]}
        self.assertEqual(available, {"azure-architect": True, "terraform-expert-engineer": True,
                                     "pr-reviewer": False, "cost-analyzer": False})
        self.assertEqual(discovery["client"], "claude-code")
        sb.wf("init", "--client", "codex", "--mode", "selected", "--agents", "cost-analyzer,azure-architect",
              "--workflow-id", "wf-c", "--objective", "t")
        state = json.loads((sb.repo / ".agentic/workflows/wf-c/WORKFLOW.json").read_text(encoding="utf-8"))
        self.assertEqual(state["client"], "codex")
        self.assertEqual({n["id"]: n["status"] for n in state["nodes"]},
                         {"cost-analyzer": "queued", "azure-architect": "blocked"})

    def test_generated_orchestrators_are_never_registered_as_specialists(self):
        sb = self.sb
        sb.write(".claude/agents/new-orch.md",
                 "---\nname: agentic-orchestrator-anthropic-claude-code\ndescription: orchestrator\n---\n", base=sb.home)
        sb.write(".codex/agents/orch.toml", 'name = "agentic-orchestrator-openai-codex"\ndescription = "o"\n', base=sb.home)
        self.assertEqual(sb.wf("registry").returncode, 0)
        ids = {a["id"] for a in json.loads(sb.wf("discover").stdout)["agents"]}
        self.assertFalse(any(i.startswith("agentic-orchestrator-") for i in ids), ids)

    def test_user_agent_folders_follow_the_client_variables(self):
        sb = self.sb
        moved = sb.base / "claude-elsewhere"
        sb.write("agents/moved.md", "---\nname: moved-agent\ndescription: m\n---\n", base=moved)
        env = sb.env()
        env["CLAUDE_CONFIG_DIR"] = str(moved)
        run = subprocess.run([sys.executable, str(sb.repo / "tooling" / "workflow.py"), "--root", str(sb.repo),
                              "registry"], env=env, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        registry = (sb.repo / "tooling" / "agent-registry.yml").read_text(encoding="utf-8")
        self.assertIn("agent_name: moved-agent", registry)
        self.assertNotIn("agent_name: terraform-expert-engineer", registry)

    def test_repository_gates_file_wins_over_the_one_beside_the_controller(self):
        sb = self.sb
        pack = sb.base / "pack"
        shutil.copytree(sb.repo / "tooling", pack / "tooling")
        shutil.rmtree(sb.repo / "tooling")
        (pack / "tooling" / "gates.json").write_text(json.dumps({"profiles": {"pack-only": {
            "detect": {"any_file": ["main.tf"]}, "gates": [{"id": "pack-gate", "command": ["definitely-not-a-tool"]}]}}}),
            encoding="utf-8")
        sb.write("tooling/gates.json", json.dumps({"profiles": {"repo-only": {
            "detect": {"any_file": ["main.tf"]}, "gates": [{"id": "repo-gate", "command": ["definitely-not-a-tool"]}]}}}))

        def pack_wf(*args):
            return subprocess.run([sys.executable, str(pack / "tooling" / "workflow.py"), "--root", str(sb.repo), *args],
                                  cwd=sb.repo, env=sb.env(), capture_output=True, text=True)
        self.assertEqual(pack_wf("registry").returncode, 0)
        pack_wf("init", "--mode", "selected", "--agents", "azure-architect", "--workflow-id", "wf-g", "--objective", "t")
        results = json.loads(pack_wf("gates", "--workflow", "wf-g").stdout)["results"]
        self.assertIn("repo-gate", [r["gate"] for r in results])
        self.assertNotIn("pack-gate", [r["gate"] for r in results])

    def test_lifecycle_blocks_then_completes_with_hashed_evidence(self):
        sb = self.sb
        sb.wf("init", "--mode", "selected", "--agents", "azure-architect", "--workflow-id", "wf-a", "--objective", "t")
        self.assertEqual(sb.wf("validate", "--workflow", "wf-a").returncode, 1)
        sb.handoff("wf-a", "azure-architect")
        proc = sb.wf("validate", "--workflow", "wf-a")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        report = json.loads(proc.stdout)
        self.assertEqual(report["workflow_status"], "completed")
        index = report["results"][0]["evidence_index"][0]
        self.assertTrue(index["exists"])
        self.assertEqual(len(index["sha256"]), 64)

    def test_rejects_paths_outside_the_repository(self):
        sb = self.sb
        sb.wf("init", "--mode", "selected", "--agents", "azure-architect", "--workflow-id", "wf-b", "--objective", "t")
        for bad in ("../outside.txt", "/etc/passwd", "C:/Windows/win.ini"):
            sb.handoff("wf-b", "azure-architect", evidence_path=bad)
            report = json.loads(sb.wf("validate", "--workflow", "wf-b").stdout)
            self.assertEqual(report["workflow_status"], "blocked", bad)
            self.assertTrue(any("repository" in e for e in report["errors"]), report["errors"])

    def test_completed_handoff_must_cite_an_existing_file(self):
        sb = self.sb
        sb.wf("init", "--mode", "selected", "--agents", "azure-architect", "--workflow-id", "wf-c", "--objective", "t")
        sb.handoff("wf-c", "azure-architect", evidence_path="does-not-exist.tf")
        report = json.loads(sb.wf("validate", "--workflow", "wf-c").stdout)
        self.assertIn("azure-architect: completed handoff cites no existing evidence or artifact file", report["errors"])

    def test_required_gates_block_until_they_pass(self):
        sb = self.sb
        sb.write("tooling/gates.json", json.dumps({"disable": ["terraform"], "profiles": {
            "custom": {"detect": {"any_file": ["main.tf"]},
                       "gates": [{"id": "always-ok", "command": ["{python}", "-c", "print('ok')"]}]}}}))
        sb.wf("init", "--mode", "selected", "--agents", "azure-architect", "--workflow-id", "wf-g",
              "--objective", "t", "--require-gates")
        sb.handoff("wf-g", "azure-architect")
        before = json.loads(sb.wf("validate", "--workflow", "wf-g").stdout)
        self.assertEqual(before["workflow_status"], "blocked")
        gates = sb.wf("gates", "--workflow", "wf-g")
        self.assertEqual(gates.returncode, 0, gates.stdout + gates.stderr)
        result = json.loads(gates.stdout)["results"][0]
        self.assertEqual(result["status"], "passed")
        self.assertTrue((sb.repo / result["evidence_path"]).is_file())
        after = json.loads(sb.wf("validate", "--workflow", "wf-g").stdout)
        self.assertEqual(after["workflow_status"], "completed", after["errors"])

    def test_failed_blocking_gate_blocks_validation(self):
        sb = self.sb
        sb.write("tooling/gates.json", json.dumps({"disable": ["terraform"], "profiles": {
            "custom": {"detect": {"any_file": ["main.tf"]},
                       "gates": [{"id": "always-fails", "command": ["{python}", "-c", "import sys; sys.exit(3)"]}]}}}))
        sb.wf("init", "--mode", "selected", "--agents", "azure-architect", "--workflow-id", "wf-f", "--objective", "t")
        sb.handoff("wf-f", "azure-architect")
        self.assertEqual(sb.wf("gates", "--workflow", "wf-f").returncode, 1)
        report = json.loads(sb.wf("validate", "--workflow", "wf-f").stdout)
        self.assertEqual(report["workflow_status"], "blocked")
        self.assertTrue(any(e.startswith("gate failed: always-fails") for e in report["errors"]))

    def test_evidence_edited_after_acceptance_goes_stale_until_restored(self):
        sb = self.sb
        sb.wf("init", "--mode", "selected", "--agents", "azure-architect", "--workflow-id", "wf-x", "--objective", "t")
        sb.handoff("wf-x", "azure-architect")
        self.assertEqual(json.loads(sb.wf("validate", "--workflow", "wf-x").stdout)["workflow_status"], "completed")
        reviewed = (sb.repo / "main.tf").read_text(encoding="utf-8")
        sb.write("main.tf", "terraform { edited after review }\n")
        stale = json.loads(sb.wf("validate", "--workflow", "wf-x").stdout)
        self.assertEqual(stale["workflow_status"], "blocked")
        self.assertTrue(any("main.tf changed since the handoff was accepted" in e for e in stale["errors"]), stale["errors"])
        sb.write("main.tf", reviewed)
        self.assertEqual(json.loads(sb.wf("validate", "--workflow", "wf-x").stdout)["workflow_status"], "completed")

    def test_evidence_modified_after_the_handoff_was_written_blocks(self):
        sb = self.sb
        sb.wf("init", "--mode", "selected", "--agents", "azure-architect", "--workflow-id", "wf-m", "--objective", "t")
        handoff = sb.handoff("wf-m", "azure-architect")
        later = handoff.stat().st_mtime + 60
        os.utime(sb.repo / "main.tf", (later, later))
        report = json.loads(sb.wf("validate", "--workflow", "wf-m").stdout)
        self.assertEqual(report["workflow_status"], "blocked")
        self.assertTrue(any("main.tf was modified after the handoff was written" in e for e in report["errors"]), report["errors"])

    def test_sha256_recorded_in_the_handoff_decides(self):
        sb = self.sb
        sb.wf("init", "--mode", "selected", "--agents", "azure-architect", "--workflow-id", "wf-h2", "--objective", "t")
        digest = hashlib.sha256((sb.repo / "main.tf").read_bytes()).hexdigest()
        handoff = sb.handoff("wf-h2", "azure-architect")
        handoff.write_text(handoff.read_text(encoding="utf-8").replace(
            "    detail: Reviewed configuration.\n", f"    detail: Reviewed configuration.\n    sha256: {digest}\n"), encoding="utf-8")
        later = handoff.stat().st_mtime + 60
        os.utime(sb.repo / "main.tf", (later, later))
        self.assertEqual(json.loads(sb.wf("validate", "--workflow", "wf-h2").stdout)["workflow_status"], "completed")
        sb.write("main.tf", "terraform { different }\n")
        report = json.loads(sb.wf("validate", "--workflow", "wf-h2").stdout)
        self.assertEqual(report["workflow_status"], "blocked")
        self.assertTrue(any("no longer matches the sha256 recorded in the handoff" in e for e in report["errors"]), report["errors"])

    def test_reverting_a_fix_after_gates_passed_makes_gates_stale(self):
        sb = self.sb
        sb.write("tooling/gates.json", json.dumps({"disable": ["terraform"], "profiles": {
            "custom": {"detect": {"any_file": ["main.tf"]},
                       "gates": [{"id": "always-ok", "command": ["{python}", "-c", "print('ok')"]}]}}}))
        sb.write("app.py", "FIXED = True\n")
        sb.wf("init", "--mode", "selected", "--agents", "azure-architect", "--workflow-id", "wf-r",
              "--objective", "t", "--require-gates")
        sb.handoff("wf-r", "azure-architect")
        self.assertEqual(sb.wf("gates", "--workflow", "wf-r").returncode, 0)
        self.assertEqual(json.loads(sb.wf("validate", "--workflow", "wf-r").stdout)["workflow_status"], "completed")
        sb.write("app.py", "FIXED = False\n")
        stale = json.loads(sb.wf("validate", "--workflow", "wf-r").stdout)
        self.assertEqual(stale["workflow_status"], "blocked")
        self.assertTrue(any(e.startswith("gate results are stale") for e in stale["errors"]), stale["errors"])
        self.assertEqual(sb.wf("export", "--workflow", "wf-r").returncode, 0)
        manifest = json.loads((sb.repo / ".agentic/workflows/wf-r/run-manifest.json").read_text(encoding="utf-8"))
        self.assertIn("stale", manifest["gates"][0]["summary"])
        self.assertEqual(sb.wf("gates", "--workflow", "wf-r").returncode, 0)
        self.assertEqual(json.loads(sb.wf("validate", "--workflow", "wf-r").stdout)["workflow_status"], "completed")

    @unittest.skipUnless(shutil.which("git"), "git is not installed")
    def test_gates_survive_a_commit_but_not_an_edit_in_a_git_repository(self):
        sb = self.sb
        sb.write("tooling/gates.json", json.dumps({"disable": ["terraform"], "profiles": {
            "custom": {"detect": {"any_file": ["main.tf"]},
                       "gates": [{"id": "always-ok", "command": ["{python}", "-c", "print('ok')"]}]}}}))
        sb.write("app.py", "FIXED = True\n")

        def git(*args):
            return subprocess.run(["git", "-c", "user.email=t@example.invalid", "-c", "user.name=t", *args],
                                  cwd=sb.repo, capture_output=True, text=True, check=True)
        git("init", "-q")
        git("add", "-A")
        git("commit", "-q", "-m", "base")
        sb.wf("init", "--mode", "selected", "--agents", "azure-architect", "--workflow-id", "wf-git",
              "--objective", "t", "--require-gates")
        sb.handoff("wf-git", "azure-architect")
        self.assertEqual(sb.wf("gates", "--workflow", "wf-git").returncode, 0)
        git("add", "-A")
        git("commit", "-q", "-m", "record the workflow")
        self.assertEqual(json.loads(sb.wf("validate", "--workflow", "wf-git").stdout)["workflow_status"], "completed")
        sb.write("app.py", "FIXED = False\n")
        stale = json.loads(sb.wf("validate", "--workflow", "wf-git").stdout)
        self.assertTrue(any(e.startswith("gate results are stale") for e in stale["errors"]), stale["errors"])

    def test_handoff_that_reports_blocked_does_not_complete(self):
        sb = self.sb
        sb.wf("init", "--mode", "selected", "--agents", "azure-architect", "--workflow-id", "wf-k", "--objective", "t")
        handoff = sb.handoff("wf-k", "azure-architect", status="blocked")
        handoff.write_text(handoff.read_text(encoding="utf-8").replace("next_action: none", "next_action: Grant read access"),
                           encoding="utf-8")
        report = json.loads(sb.wf("validate", "--workflow", "wf-k").stdout)
        self.assertEqual(report["workflow_status"], "blocked")
        self.assertIn("azure-architect: the agent reported blocked: Grant read access", report["errors"])

    def test_missing_gate_tool_is_skipped_not_failed(self):
        sb = self.sb
        sb.write("tooling/gates.json", json.dumps({"profiles": {"ghost": {
            "detect": {"any_file": ["main.tf"]},
            "gates": [{"id": "ghost-tool", "command": ["definitely-not-a-real-tool-xyz"]}]}}}))
        sb.wf("init", "--mode", "selected", "--agents", "azure-architect", "--workflow-id", "wf-s", "--objective", "t")
        results = json.loads(sb.wf("gates", "--workflow", "wf-s", "--profiles", "ghost").stdout)["results"]
        self.assertEqual(results[0]["status"], "skipped")

    def test_export_matches_code_conductor_contract_and_respects_boundary(self):
        sb = self.sb
        sb.wf("init", "--mode", "selected", "--agents", "azure-architect,cost-analyzer,ghost",
              "--optional-agents", "ghost", "--workflow-id", "wf-e", "--objective", "Export test",
              "--risk", "R2", "--acceptance", "plan reviewed; risks listed")
        sb.handoff("wf-e", "azure-architect")
        self.assertEqual(sb.wf("export", "--workflow", "wf-e").returncode, 0)
        manifest = json.loads((sb.repo / ".agentic/workflows/wf-e/run-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(schema_errors(manifest, SCHEMA["$defs"]["RunManifest"]), [])
        self.assertNotIn("mergeDecision", manifest)
        self.assertEqual(manifest["task"]["risk"], "R2")
        self.assertEqual(manifest["task"]["acceptanceCriteria"], ["plan reviewed", "risks listed"])
        by_agent = {r["agentId"]: r for r in manifest["results"]}
        self.assertEqual(by_agent["azure-architect"]["notVerified"], ["Live deployment was not performed."])
        self.assertEqual(by_agent["azure-architect"]["findings"][0]["blocking"], True)
        self.assertEqual(by_agent["cost-analyzer"]["status"], "blocked")
        self.assertTrue(all(r["recommendation"] != "ready" for r in manifest["results"]))
        self.assertIn("skipped_optional: ghost", manifest["task"]["constraints"])

    def test_hook_redacts_payload_and_emits_json_on_stop(self):
        sb = self.sb
        payload = {"hook_event_name": "Stop", "cwd": str(sb.repo), "session_id": "s1",
                   "prompt": "my secret token is abc123", "last_assistant_message": "secret",
                   "tool_input": {"command": "cat .env"}}
        proc = sb.hook(payload)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(json.loads(proc.stdout), {})
        log = (sb.repo / ".agentic/audit/claude-events.jsonl").read_text(encoding="utf-8")
        self.assertNotIn("abc123", log)
        self.assertNotIn("cat .env", log)
        record = json.loads(log.splitlines()[-1])
        self.assertEqual(record["event"]["session_id"], "s1")
        self.assertIn("prompt", record["event"]["dropped_keys"])
        self.assertTrue((sb.repo / ".agentic/.gitignore").is_file())

    def test_stop_guard_blocks_only_when_enforced_and_fails_open(self):
        sb = self.sb
        sb.wf("init", "--mode", "selected", "--agents", "azure-architect", "--workflow-id", "wf-h",
              "--objective", "t", "--enforce-stop")
        blocked = json.loads(sb.hook({"cwd": str(sb.repo)}, "--event", "Stop").stdout)
        self.assertEqual(blocked.get("decision"), "block")
        shutil.move(str(sb.repo / "tooling"), str(sb.base / "tooling-aside"))
        self.assertEqual(json.loads(sb.hook({"cwd": str(sb.repo)}, "--event", "Stop").stdout), {})

    def test_stop_guard_uses_the_controller_installed_in_the_pack_home(self):
        sb = self.sb
        sb.wf("init", "--mode", "selected", "--agents", "azure-architect", "--workflow-id", "wf-p",
              "--objective", "t", "--enforce-stop")
        pack = sb.base / "pack"
        shutil.move(str(sb.repo / "tooling"), str(pack / "tooling"))
        shutil.move(str(sb.repo / "hooks"), str(pack / "hooks"))
        proc = subprocess.run([sys.executable, str(pack / "hooks" / "claude_event.py"), "--event", "Stop"],
                              input=json.dumps({"cwd": str(sb.repo)}), cwd=sb.repo, env=sb.env(),
                              capture_output=True, text=True)
        decision = json.loads(proc.stdout)
        self.assertEqual(decision.get("decision"), "block")
        # The hook names the resolved path; Windows runners give temp folders a short 8.3 alias otherwise.
        self.assertIn((pack / "tooling" / "workflow.py").resolve().as_posix(), decision["reason"])

    def test_doctor_reports_install_health(self):
        sb = self.sb
        healthy = sb.wf("doctor")
        self.assertEqual(healthy.returncode, 0, healthy.stdout)
        self.assertIn("orchestrator agent for claude-code: installed", healthy.stdout)
        (sb.home / ".claude/agents/orch.md").unlink()
        broken = sb.wf("doctor")
        self.assertEqual(broken.returncode, 1)
        self.assertIn("not installed for any client", broken.stdout)

    def test_registry_reads_wrapped_descriptions_and_trims_at_a_word(self):
        sb = self.sb
        sb.write(".claude/agents/wrapped.md", "---\nname: wrapped-agent\ndescription: Reviews infrastructure changes\n"
                 "  across Terraform and Bicep\n  without editing files.\ntools:\n- Read\n---\nbody\n")
        sb.write(".claude/agents/folded.md", "---\nname: folded-agent\ndescription: >\n  Folded text\n  on two lines.\n---\n")
        long_words = " ".join(["capability"] * 60)
        sb.write(".claude/agents/long.md", f"---\nname: long-agent\ndescription: {long_words}\n---\n")
        self.assertEqual(sb.wf("registry").returncode, 0)
        text = (sb.repo / "tooling" / "agent-registry.yml").read_text(encoding="utf-8")
        self.assertIn('capability: "Reviews infrastructure changes across Terraform and Bicep without editing files."', text)
        self.assertIn('capability: "Folded text on two lines."', text)
        value = next(line for line in text.splitlines()
                     if line.strip().startswith('capability: "capability')).split('"')[1]
        self.assertTrue(value.endswith("..."), value)
        kept = value[:-3]
        self.assertTrue(long_words.startswith(kept))
        self.assertEqual(long_words[len(kept)], " ", "trimmed mid-word")
        self.assertLessEqual(len(kept), 240)

    def test_doctor_states_hook_status_truthfully(self):
        sb = self.sb
        out = sb.wf("doctor").stdout
        self.assertIn(".codex/hooks.json not active", out)
        self.assertIn("Claude hook entries not merged", out)
        self.assertIn("AGENTS.md has no orchestration section", out)
        sb.write(".codex/hooks.json", "{}")
        self.assertIn(".codex/hooks.json present", sb.wf("doctor").stdout)

    def test_invalid_workflow_id_is_rejected(self):
        proc = self.sb.wf("init", "--mode", "one", "--workflow-id", "../escape", "--objective", "t")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("invalid workflow id", proc.stderr)


class BoundaryTests(unittest.TestCase):
    """Code Workflow must never orchestrate other providers (Code Conductor ADR 0011)."""

    PROVIDER_CLIS = {"claude", "codex", "copilot", "kiro", "kiro-cli", "gemini", "gh", "antigravity"}

    def test_tooling_never_spawns_provider_clis(self):
        for source in (PAYLOAD / "tooling" / "workflow.py", PAYLOAD / "hooks" / "claude_event.py"):
            tree = ast.parse(source.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and getattr(node.func, "attr", "") in {"run", "Popen", "call", "check_output"}:
                    if node.args and isinstance(node.args[0], ast.List) and node.args[0].elts:
                        first = node.args[0].elts[0]
                        if isinstance(first, ast.Constant):
                            self.assertNotIn(first.value, self.PROVIDER_CLIS, f"{source.name} spawns {first.value}")

    def test_builtin_gates_are_deterministic_tools_only(self):
        sys.path.insert(0, str(PAYLOAD / "tooling"))
        try:
            import workflow  # noqa: PLC0415
        finally:
            sys.path.pop(0)
        for profile in workflow.BUILTIN_GATE_PROFILES.values():
            for gate in profile["gates"]:
                self.assertNotIn(gate["command"][0], self.PROVIDER_CLIS)

    def test_export_never_claims_readiness(self):
        source = (PAYLOAD / "tooling" / "workflow.py").read_text(encoding="utf-8")
        export_body = source.split("def export_workflow", 1)[1].split("\ndef ", 1)[0]
        self.assertNotIn('"ready"', export_body)
        self.assertNotIn('"mergeDecision"', export_body)


class PackTests(unittest.TestCase):
    def test_skills_are_complete_and_well_formed(self):
        skills = ROOT / "user-claude" / "skills"
        self.assertEqual(sorted(p.name for p in skills.iterdir() if p.is_dir()), sorted(EXPECTED_SKILLS))
        for name in EXPECTED_SKILLS:
            text = (skills / name / "SKILL.md").read_text(encoding="utf-8")
            match = re.match(r"\A---\nname: ([a-z0-9-]+)\ndescription: (.+?)\n---\n", text)
            self.assertIsNotNone(match, name)
            self.assertEqual(match.group(1), name)
            self.assertLessEqual(len(match.group(2)), 1024)
            for link in re.findall(r"\]\((references/[^)]+)\)", text):
                self.assertTrue((skills / name / link).is_file(), f"{name} links missing {link}")

    def test_client_agents_share_one_contract(self):
        claude = (ROOT / "user-claude/agents/claude-agentic-orchestrator.md").read_text(encoding="utf-8")
        codex = (ROOT / "user-codex/agents/claude-agentic-orchestrator.toml").read_text(encoding="utf-8")
        copilot = (ROOT / "user-copilot/agents/claude-agentic-orchestrator.agent.md").read_text(encoding="utf-8")
        for text in (claude, codex, copilot):
            self.assertIn("claude-agentic-orchestrator", text)
            for phrase in ("workflow.py init", "workflow.py gates", "validate", "handoffs/<agent-id>.yml"):
                self.assertTrue(phrase in text or phrase.replace("workflow.py ", "tooling/workflow.py ") in text,
                                f"missing {phrase!r}")
        self.assertIn("simulate delegation", codex)
        self.assertIn("simulate delegation", copilot)
        if sys.version_info >= (3, 11):
            import tomllib  # noqa: PLC0415
            data = tomllib.loads(codex)
            self.assertEqual(sorted(data), ["description", "developer_instructions", "name"])

    def test_hook_samples_and_settings_are_valid_json(self):
        for rel in (".claude/settings.agentic-orchestrator.json", ".codex/hooks.sample.json",
                    ".github/hooks/agentic-orchestrator.sample.json"):
            json.loads((PAYLOAD / rel).read_text(encoding="utf-8"))
        copilot = json.loads((PAYLOAD / ".github/hooks/agentic-orchestrator.sample.json").read_text(encoding="utf-8"))
        self.assertEqual(copilot["version"], 1)
        for entries in copilot["hooks"].values():
            for entry in entries:
                self.assertIn("timeoutSec", entry)

    @unittest.skipIf(os.name == "nt", "bash syntax check runs on POSIX runners")
    def test_install_sh_syntax(self):
        self.assertEqual(subprocess.run(["bash", "-n", str(ROOT / "install.sh")]).returncode, 0)

    def test_install_sh_avoids_bash4_features(self):
        text = (ROOT / "install.sh").read_text(encoding="utf-8")
        for token in ("mapfile", "readarray", "declare -A"):
            self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
