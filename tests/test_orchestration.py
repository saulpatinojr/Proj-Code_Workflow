"""Orchestration generator suite: deterministic output, safe writes, and the Claude Code, Codex and
GitHub Copilot templates."""
from __future__ import annotations

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
GENERATOR = ROOT / "orchestration" / "generate.py"
SKILLS = ROOT / "orchestration" / "skills"
ORCHESTRATOR = "agentic-orchestrator-anthropic-claude-code"
COPILOT_ORCHESTRATOR = "agentic-orchestrator-github-copilot"
CODEX_ORCHESTRATOR = "agentic-orchestrator-openai-codex"
TEMPLATES = ROOT / "orchestration" / "templates"
SKILL_NAMES = sorted(p.name for p in SKILLS.iterdir() if p.is_dir())
PLACEHOLDERS = {"name", "tools", "skills", "controller", "pack_home", "roster"}


def frontmatter(text: str) -> dict:
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    assert match, "missing frontmatter"
    fields, key = {}, None
    for line in match.group(1).splitlines():
        if line.startswith("  - ") and key:
            fields.setdefault(key, []).append(line[4:])
        else:
            key, _, value = line.partition(":")
            if value.strip():
                fields[key] = value.strip()
    return fields


class Profile:
    """A fake user profile with Claude Code installed and a few specialists."""

    def __init__(self):
        self.base = Path(tempfile.mkdtemp(prefix="cw-orch-"))
        self.home = self.base / "home"
        self.claude = self.home / ".claude"
        self.pack = self.home / ".code-workflow"
        self.write(self.claude / "agents" / "tf.md",
                   "---\nname: terraform-expert-engineer\ndescription: Terraform and HCL modules\n---\nbody\n")
        self.write(self.claude / "agents" / "team" / "az.md",
                   "---\nname: azure-architect\ndescription: Azure landing zones\n---\nbody\n")
        self.extra_env = {}

    @staticmethod
    def write(path: Path, text: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def env(self):
        env = dict(os.environ)
        env["HOME"] = str(self.home)
        env["USERPROFILE"] = str(self.home)
        for var in ("CLAUDE_CONFIG_DIR", "CODE_WORKFLOW_HOME", "CODEX_HOME", "COPILOT_HOME", "KIRO_HOME",
                    "CLAUDE_PROJECT_DIR"):
            env.pop(var, None)
        env.update(self.extra_env)
        return env

    def generate(self, *args):
        return subprocess.run([sys.executable, str(GENERATOR), *args], env=self.env(), capture_output=True, text=True)

    def controller(self, *args, cwd=None):
        return subprocess.run([sys.executable, str(self.pack / "tooling" / "workflow.py"), *args],
                              cwd=cwd, env=self.env(), capture_output=True, text=True)

    def manifest(self) -> dict:
        return json.loads((self.pack / "generated.json").read_text(encoding="utf-8"))["files"]

    def snapshot(self) -> dict:
        return {p: p.read_bytes() for p in sorted(self.home.rglob("*")) if p.is_file() and "agent-registry" not in p.name}

    def cleanup(self):
        def unlock_and_retry(func, path, *_):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        if sys.version_info >= (3, 12):
            shutil.rmtree(self.base, onexc=unlock_and_retry)
        else:
            shutil.rmtree(self.base, onerror=unlock_and_retry)

    def add_copilot(self):
        self.copilot = self.home / ".copilot"
        self.write(self.copilot / "agents" / "gh.agent.md",
                   "---\nname: github-expert-engineer\ndescription: GitHub platform work\n---\nbody\n")
        self.write(self.copilot / "agents" / "docs.md", "---\ndescription: Documentation archivist\n---\nbody\n")

    def add_codex(self):
        self.codex = self.home / ".codex"
        self.write(self.codex / "agents" / "cost.toml",
                   'name = "cost-analyzer"\ndescription = "FinOps"\ndeveloper_instructions = """x"""\n')

    def shared_skills(self) -> Path:
        return self.home / ".agents" / "skills"


class GeneratorTests(unittest.TestCase):
    def setUp(self):
        self.p = Profile()

    def tearDown(self):
        self.p.cleanup()

    def test_generates_the_claude_code_orchestration(self):
        result = self.p.generate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        agent = (self.p.claude / "agents" / f"{ORCHESTRATOR}.md").read_text(encoding="utf-8")
        fields = frontmatter(agent)
        self.assertEqual(fields["name"], ORCHESTRATOR)
        self.assertLessEqual(len(fields["description"]), 1024)
        self.assertEqual(fields["skills"], SKILL_NAMES)
        tools = [t.strip() for t in fields["tools"].split(",")]
        self.assertIn("Agent", tools)
        self.assertEqual("PowerShell" in tools, os.name == "nt")
        controller = (self.p.pack / "tooling" / "workflow.py").as_posix()
        self.assertIn(f'"{controller}" discover --client claude-code', agent)
        self.assertIn(f'"{controller}" init --client claude-code', agent)
        roster = agent.split("## Specialists installed in Claude Code", 1)[1]
        self.assertEqual(re.findall(r"^- `([^`]+)`", roster, re.M), ["azure-architect", "terraform-expert-engineer"])
        self.assertTrue((self.p.claude / "rules" / "code-workflow.md").is_file())
        for name in SKILL_NAMES:
            skill = (self.p.claude / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertEqual(frontmatter(skill)["name"], name)
        for path in self.p.home.rglob("*"):
            if path.is_file() and path.suffix in (".md", ".json"):
                self.assertNotIn("{{", path.read_text(encoding="utf-8"), path)
        for source, target in (("repo-root/tooling/workflow.py", "tooling/workflow.py"),
                               ("repo-root/hooks/claude_event.py", "hooks/claude_event.py")):
            expected = (ROOT / source).read_text(encoding="utf-8").replace("\r\n", "\n")
            self.assertEqual((self.p.pack / target).read_bytes(), expected.encode("utf-8"))

    def test_hook_configuration_is_written_but_not_turned_on(self):
        self.p.generate()
        settings = json.loads((self.p.pack / "hooks" / "claude-code.settings.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(settings["hooks"]), ["SessionStart", "Stop", "SubagentStart", "SubagentStop"])
        script = (self.p.pack / "hooks" / "claude_event.py").as_posix()
        for entries in settings["hooks"].values():
            self.assertIn(f'"{script}" --event', entries[0]["hooks"][0]["command"])
        self.assertFalse((self.p.claude / "settings.json").exists())

    def test_manifest_records_every_file_with_its_hash(self):
        self.p.generate()
        manifest = self.p.manifest()
        self.assertEqual(len(manifest), 2 + 1 + 1 + 1 + sum(1 for p in SKILLS.rglob("*") if p.is_file()))
        for key, entry in manifest.items():
            self.assertEqual(hashlib.sha256(Path(key).read_bytes()).hexdigest(), entry["sha256"], key)
            self.assertIn(entry["owner"], ("pack", "claude-code"))

    def test_second_run_changes_nothing(self):
        self.p.generate()
        before = self.p.snapshot()
        result = self.p.generate()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.p.snapshot(), before)
        self.assertNotIn("create", result.stdout)
        self.assertNotIn("update", result.stdout)

    def test_new_specialist_updates_the_roster(self):
        self.p.generate()
        self.p.write(self.p.claude / "agents" / "docs.md", "---\nname: docs-writer\ndescription: Docs\n---\n")
        result = self.p.generate()
        self.assertIn("update", result.stdout)
        agent = (self.p.claude / "agents" / f"{ORCHESTRATOR}.md").read_text(encoding="utf-8")
        self.assertIn("- `docs-writer`: Docs", agent)

    def test_dry_run_writes_nothing(self):
        before = self.p.snapshot()
        result = self.p.generate("--dry-run")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Dry run", result.stdout)
        self.assertEqual(self.p.snapshot(), before)
        self.assertFalse(self.p.pack.exists())

    def test_a_changed_file_stops_the_client_and_nothing_is_written(self):
        self.p.generate()
        rule = self.p.claude / "rules" / "code-workflow.md"
        rule.write_text(rule.read_text(encoding="utf-8") + "my note\n", encoding="utf-8")
        self.p.write(self.p.claude / "agents" / "docs.md", "---\nname: docs-writer\ndescription: Docs\n---\n")
        before = self.p.snapshot()
        result = self.p.generate()
        self.assertEqual(result.returncode, 1)
        self.assertIn("changed since Code Workflow wrote it", result.stdout)
        self.assertEqual(self.p.snapshot(), before)

    def test_a_file_it_did_not_write_is_never_overwritten(self):
        target = self.p.write(self.p.claude / "agents" / f"{ORCHESTRATOR}.md", "---\nname: mine\ndescription: x\n---\n")
        result = self.p.generate()
        self.assertEqual(result.returncode, 1)
        self.assertIn("not written by Code Workflow", result.stdout)
        self.assertEqual(target.read_text(encoding="utf-8"), "---\nname: mine\ndescription: x\n---\n")
        self.assertFalse((self.p.claude / "skills").exists())

    def test_legacy_install_is_replaced_only_on_request_and_backed_up(self):
        legacy_agent = self.p.write(self.p.claude / "agents" / "claude-agentic-orchestrator.md",
                                    "---\nname: claude-agentic-orchestrator\ndescription: old\n---\n")
        self.p.write(self.p.claude / "skills" / "agentic-workflow-dispatch" / "SKILL.md", "old dispatch\n")
        self.p.write(self.p.claude / "skills" / "claude-hooks-and-guardrails" / "SKILL.md", "old hooks\n")
        refused = self.p.generate()
        self.assertEqual(refused.returncode, 1)
        self.assertIn("--replace-legacy", refused.stdout)
        self.assertTrue(legacy_agent.is_file())
        replaced = self.p.generate("--replace-legacy")
        self.assertEqual(replaced.returncode, 0, replaced.stdout + replaced.stderr)
        self.assertFalse(legacy_agent.exists())
        self.assertFalse((self.p.claude / "skills" / "claude-hooks-and-guardrails").exists())
        dispatch = (self.p.claude / "skills" / "agentic-workflow-dispatch" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: agentic-workflow-dispatch", dispatch)
        backups = sorted(p.relative_to(self.p.pack).as_posix() for p in (self.p.pack / "backup").rglob("*") if p.is_file())
        self.assertEqual([b.split("/", 2)[2] for b in backups],
                         ["claude-code/agents/claude-agentic-orchestrator.md",
                          "claude-code/skills/agentic-workflow-dispatch/SKILL.md",
                          "claude-code/skills/claude-hooks-and-guardrails/SKILL.md"])

    def test_files_it_no_longer_generates_are_removed_if_unchanged(self):
        self.p.generate()
        stale = self.p.write(self.p.claude / "skills" / "retired-skill" / "SKILL.md", "retired\n")
        manifest_path = self.p.pack / "generated.json"
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        data["files"][stale.as_posix()] = {"sha256": hashlib.sha256(stale.read_bytes()).hexdigest(), "owner": "claude-code"}
        manifest_path.write_text(json.dumps(data), encoding="utf-8")
        result = self.p.generate()
        self.assertIn("remove", result.stdout)
        self.assertFalse(stale.exists())
        self.assertFalse(stale.parent.exists())
        self.assertNotIn(stale.as_posix(), self.p.manifest())

    def test_claude_config_dir_moves_the_client_home(self):
        moved = self.p.base / "elsewhere"
        shutil.move(str(self.p.claude), str(moved))
        self.p.extra_env = {"CLAUDE_CONFIG_DIR": str(moved)}
        result = self.p.generate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        agent = (moved / "agents" / f"{ORCHESTRATOR}.md").read_text(encoding="utf-8")
        self.assertIn("`terraform-expert-engineer`", agent)
        self.assertFalse(self.p.claude.exists())

    def test_generated_controller_delegates_only_within_its_client(self):
        self.p.generate()
        self.p.write(self.p.home / ".codex" / "agents" / "cost.toml",
                     'name = "cost-analyzer"\ndescription = "FinOps"\ndeveloper_instructions = """x"""\n')
        repo = self.p.base / "repo"
        repo.mkdir()
        self.assertEqual(self.p.controller("--root", str(repo), "registry").returncode, 0)
        discovery = json.loads(self.p.controller("--root", str(repo), "discover", "--client", "claude-code").stdout)
        available = {a["id"]: a["available"] for a in discovery["agents"]}
        self.assertEqual(available, {"azure-architect": True, "cost-analyzer": False, "terraform-expert-engineer": True})
        self.assertTrue((repo / ".agentic" / "discovery.json").is_file())
        self.assertFalse((self.p.pack / ".agentic").exists())


class CopilotAndCodexTests(unittest.TestCase):
    def setUp(self):
        self.p = Profile()
        self.p.add_copilot()
        self.p.add_codex()

    def tearDown(self):
        self.p.cleanup()

    def assert_shared_skills(self, base: Path):
        for name in SKILL_NAMES:
            skill = (base / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertEqual(frontmatter(skill)["name"], name)
            self.assertNotIn("{{", skill)

    def test_generates_the_copilot_orchestration(self):
        result = self.p.generate("--client", "github-copilot")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        agent = (self.p.copilot / "agents" / f"{COPILOT_ORCHESTRATOR}.agent.md").read_text(encoding="utf-8")
        fields = frontmatter(agent)
        self.assertEqual(fields["name"], COPILOT_ORCHESTRATOR)
        self.assertLessEqual(len(fields["description"]), 1024)
        self.assertEqual(fields["include-custom-instructions"], "true")
        self.assertEqual(sorted(re.findall(r'"([a-z]+)"', fields["tools"])),
                         ["agent", "edit", "execute", "read", "search", "todo", "web"])
        controller = (self.p.pack / "tooling" / "workflow.py").as_posix()
        self.assertIn(f'"{controller}" discover --client github-copilot', agent)
        self.assertIn(f'"{controller}" init --client github-copilot', agent)
        roster = agent.split("## Specialists installed in GitHub Copilot", 1)[1]
        self.assertEqual(re.findall(r"^- `([^`]+)`", roster, re.M), ["docs", "github-expert-engineer"])
        instructions = (self.p.copilot / "instructions" / "code-workflow.instructions.md").read_text(encoding="utf-8")
        self.assertEqual(frontmatter(instructions)["applyTo"], '"**"')
        self.assertIn(f"copilot --agent {COPILOT_ORCHESTRATOR}", instructions)
        self.assert_shared_skills(self.p.shared_skills())
        self.assertFalse((self.p.codex / "agents" / f"{CODEX_ORCHESTRATOR}.toml").exists())
        self.assertFalse((self.p.claude / "agents" / f"{ORCHESTRATOR}.md").exists())

    def test_copilot_hooks_are_written_but_not_turned_on(self):
        self.p.generate("--client", "github-copilot")
        settings = json.loads((self.p.pack / "hooks" / "github-copilot.hooks.json").read_text(encoding="utf-8"))
        self.assertEqual(settings["version"], 1)
        self.assertEqual(sorted(settings["hooks"]), ["agentStop", "sessionStart", "subagentStart", "subagentStop"])
        script = (self.p.pack / "hooks" / "claude_event.py").as_posix()
        for entries in settings["hooks"].values():
            self.assertIn(f'"{script}" --event', entries[0]["powershell"])
            self.assertEqual(entries[0]["bash"], entries[0]["powershell"])
        self.assertFalse((self.p.copilot / "hooks").exists())

    def test_copilot_home_moves_the_agent_and_its_skills(self):
        moved = self.p.base / "copilot-elsewhere"
        shutil.move(str(self.p.copilot), str(moved))
        self.p.extra_env = {"COPILOT_HOME": str(moved)}
        result = self.p.generate("--client", "github-copilot")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        agent = (moved / "agents" / f"{COPILOT_ORCHESTRATOR}.agent.md").read_text(encoding="utf-8")
        self.assertIn("`github-expert-engineer`", agent)
        self.assert_shared_skills(moved / "skills")
        self.assertFalse(self.p.shared_skills().exists())

    def test_generates_the_codex_orchestration(self):
        result = self.p.generate("--client", "codex")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        text = (self.p.codex / "agents" / f"{CODEX_ORCHESTRATOR}.toml").read_text(encoding="utf-8")
        quotes = "'" * 3
        self.assertTrue(text.startswith(f'name = "{CODEX_ORCHESTRATOR}"\ndescription = "'), text[:120])
        self.assertIn(f"\ndeveloper_instructions = {quotes}\n", text)
        self.assertTrue(text.endswith(f"\n{quotes}\n"))
        self.assertEqual(text.count(quotes), 2)
        try:
            import tomllib
        except ImportError:  # Python 3.10 and older have no TOML reader; the checks above still apply
            tomllib = None
        if tomllib:
            agent = tomllib.loads(text)
            self.assertEqual(sorted(agent), ["description", "developer_instructions", "name"])
            text = agent["developer_instructions"]
        controller = (self.p.pack / "tooling" / "workflow.py").as_posix()
        self.assertIn(f'"{controller}" discover --client codex', text)
        self.assertIn(f'"{controller}" init --client codex', text)
        roster = text.split("## Specialists installed in OpenAI Codex", 1)[1]
        self.assertEqual(re.findall(r"^- `([^`]+)`", roster, re.M), ["cost-analyzer"])
        self.assert_shared_skills(self.p.shared_skills())
        hooks = json.loads((self.p.pack / "hooks" / "codex.hooks.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(hooks["hooks"]), ["SessionStart", "Stop", "SubagentStart", "SubagentStop"])
        self.assertFalse((self.p.codex / "hooks.json").exists())

    def test_every_detected_client_shares_skills_and_a_second_run_changes_nothing(self):
        result = self.p.generate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for path in (self.p.claude / "agents" / f"{ORCHESTRATOR}.md",
                     self.p.copilot / "agents" / f"{COPILOT_ORCHESTRATOR}.agent.md",
                     self.p.codex / "agents" / f"{CODEX_ORCHESTRATOR}.toml"):
            self.assertTrue(path.is_file(), path)
        self.assertNotIn("template is not built yet", result.stdout)
        manifest = self.p.manifest()
        for key, entry in manifest.items():
            self.assertEqual(hashlib.sha256(Path(key).read_bytes()).hexdigest(), entry["sha256"], key)
        shared = self.p.shared_skills().as_posix() + "/"
        self.assertEqual(sum(1 for key in manifest if key.startswith(shared)),
                         sum(1 for p in SKILLS.rglob("*") if p.is_file()))
        before = self.p.snapshot()
        again = self.p.generate()
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        self.assertEqual(self.p.snapshot(), before)
        for word in ("create", "update", "remove"):
            self.assertNotIn(word, again.stdout)

    def test_legacy_copilot_agent_is_replaced_only_on_request(self):
        legacy = self.p.write(self.p.copilot / "agents" / "claude-agentic-orchestrator.agent.md",
                              "---\nname: claude-agentic-orchestrator\ndescription: old\n---\n")
        self.assertEqual(self.p.generate("--client", "github-copilot").returncode, 0)
        self.assertTrue(legacy.is_file())
        replaced = self.p.generate("--client", "github-copilot", "--replace-legacy")
        self.assertEqual(replaced.returncode, 0, replaced.stdout + replaced.stderr)
        self.assertFalse(legacy.exists())
        backups = [p.name for p in (self.p.pack / "backup").rglob("*") if p.is_file()]
        self.assertEqual(backups, ["claude-agentic-orchestrator.agent.md"])

    def test_generated_controller_counts_copilot_agents_for_copilot(self):
        self.p.generate("--client", "github-copilot")
        repo = self.p.base / "repo"
        repo.mkdir()
        self.assertEqual(self.p.controller("--root", str(repo), "registry").returncode, 0)
        discovery = json.loads(self.p.controller("--root", str(repo), "discover", "--client", "github-copilot").stdout)
        available = {a["id"]: a["available"] for a in discovery["agents"]}
        self.assertTrue(available["github-expert-engineer"])
        self.assertFalse(available["cost-analyzer"])
        self.assertNotIn(COPILOT_ORCHESTRATOR, available)


class TemplateTests(unittest.TestCase):
    def test_skills_are_well_formed_and_use_only_known_placeholders(self):
        self.assertEqual(SKILL_NAMES, sorted([
            "agentic-workflow-dispatch", "agent-registry-and-capability-discovery", "handoff-contract-and-state",
            "subagent-delegation", "workflow-hooks-and-guardrails", "workflow-evidence-and-recovery"]))
        for name in SKILL_NAMES:
            text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8").replace("\r\n", "\n")
            match = re.match(r"\A---\nname: ([a-z0-9-]+)\ndescription: (.+?)\n---\n", text)
            self.assertIsNotNone(match, name)
            self.assertEqual(match.group(1), name)
            self.assertLessEqual(len(match.group(2)), 1024)
            for link in re.findall(r"\]\((references/[^)]+)\)", text):
                self.assertTrue((SKILLS / name / link).is_file(), f"{name} links missing {link}")
        for path in list(SKILLS.rglob("*.md")) + [p for p in TEMPLATES.rglob("*") if p.is_file()]:
            used = set(re.findall(r"\{\{([a-z_]+)\}\}", path.read_text(encoding="utf-8")))
            self.assertLessEqual(used, PLACEHOLDERS, path)

    def test_orchestrator_carries_the_roles_without_a_readiness_verdict(self):
        reference = (SKILLS / "agentic-workflow-dispatch" / "references" / "roles-and-stances.md").read_text(encoding="utf-8")
        for stance in ("constructive", "critical", "neutral"):
            self.assertIn(f"`{stance}`", reference)
        for rule in ("never the node that built", "A stronger model does not win", "never approves or merges"):
            self.assertIn(rule, reference)
        for path in list(SKILLS.rglob("*.md")) + [p for p in TEMPLATES.rglob("*") if p.is_file()]:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("mergeDecision", text, path)
            self.assertNotIn("recommendation: ready", text, path)
        for name in ("claude-code/agent.md", "github-copilot/agent.md", "codex/agent.toml"):
            agent = (TEMPLATES / name).read_text(encoding="utf-8")
            self.assertIn("## Roles, stances and independence", agent, name)
            self.assertIn("never reviews its own output", agent, name)
            self.assertIn("never say a change is ready to merge", agent, name)

    def test_skills_never_tie_the_controller_to_a_repository_copy(self):
        for path in SKILLS.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("tooling/workflow.py", text, path)
            self.assertNotIn("CLAUDE_PROJECT_DIR", text, path)


if __name__ == "__main__":
    unittest.main()
