# Session notes

Notes carried from one working session to the next. Newest first.

## 2026-10-18, for the next session

Status at the end of the session: pull requests #4 and #5 are merged into main, and the local repository is in sync with GitHub.

The Claude Code orchestrator now generates, installs into your profile, and has run a real delegated workflow end to end in Claude Code. It's in PR #5, which passes all tests. Decision 10 (the VS Code pop-up) is recorded in PR #4, which is separate because you merged #3 before it reached that branch. Both are ready to merge.

**What PR #5 adds**

- **The generator:** `orchestration/generate.py` installs the workflow controller once in `~/.code-workflow/`. For Claude Code it writes:
  - the orchestrator `agentic-orchestrator-anthropic-claude-code`, which lists your Claude Code specialists and delegates only to them;
  - the six workflow skills, now the same for every client (the two Claude-named ones are renamed);
  - a short rule that tells every Claude Code session the orchestrator exists;
  - a hook configuration that is written but not turned on.
- **Safety:**
  - A second run changes nothing.
  - It never overwrites a file it didn't write, or one changed since it wrote it. Anything like that stops the run for that client, and the file is reported.
  - The old installer's files are replaced only on request, after a backup.

**What changed on this computer**

- I ran the generator for real. The old `claude-agentic-orchestrator` and its six skills were backed up to `~/.code-workflow/backup/20261018T231002Z/` and replaced. Open sessions keep the old list until restarted. To undo, delete the files listed in `~/.code-workflow/generated.json` and copy the backup back.
- Claude Code then ran a small real workflow with the orchestrator in a scratch folder. It handed a Terraform review to `terraform-expert-engineer`, got that agent's written report back, ran the checks, and the workflow finished as completed. Total cost was under the $5 cap I set.

**Please check one thing:** start the orchestrator from the VS Code Claude Code panel. I can't operate VS Code's interface. The panel runs its own copy of the same engine and reads the same `~/.claude` folder, so it should appear there.

**Code quality check:** qlty says it passes, but lists 9 "blocking" issues. I ran qlty locally, and none of them are in the new generator. All 9 are old complexity problems in the existing workflow controller and hook, and main has them too. They show up because this PR edits a few lines inside those functions. Cleaning them up would be a separate job.

Next, once you merge, is the Codex template, then Copilot together with the VS Code pop-up extension.

**Kept on purpose**

- `~/.code-workflow/backup/20261018T231002Z/`: the only copy of the old installer's Claude Code files, needed for an undo.
- `user-claude/`, `user-codex/`, `user-copilot/`, `repo-root/`, `install.ps1` and `install.sh`: the old installers still use them, until the local setup script (plan step 6) replaces them.
- The old installer's skills in `~/.agents/skills/` and its Codex and Copilot orchestrators: still in use until their templates replace them.
