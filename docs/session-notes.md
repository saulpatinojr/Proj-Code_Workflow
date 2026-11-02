# Session notes

Notes carried from one working session to the next. Newest first.

## 2026-11-02, for the next session

**Draw.io packs: released and installed.**

- [Proj-Agent_Packs pull request #30](https://github.com/saulpatinojr/Proj-Agent_Packs/pull/30) is merged. The [releases](https://github.com/saulpatinojr/Proj-Agent_Packs/releases) `aws-cloud-architect-v1.5.0`, `aws-expert-designer-v1.5.0`, `azure-cloud-architect-v1.5.0`, `azure-expert-designer-v1.5.0` and `google-cloud-architect-v1.3.0` are published.
- APM 0.35.0 is pinned in Proj-Agent_Packs and installed on this computer:
  - The pin is [pull request #31](https://github.com/saulpatinojr/Proj-Agent_Packs/pull/31), which closed [issue #29](https://github.com/saulpatinojr/Proj-Agent_Packs/issues/29).
  - The 0.33.0 copy is kept in APM's `releases` folder for a rollback.
- `apm install -g` put the releases into Claude Code, Codex, Copilot and Kiro. It took three runs; the progress log in `setup-design.md` explains why. Verified afterwards:
  - Every file APM's lock file records is present.
  - The five packs' skills match their source.

**Cleaned up**

- The seven Proj-Agent_Packs worktrees, and the 15 local branches whose work is in `main` (12 there, 3 here).
- The `__pycache__` folders left by test runs.
- The client workflow records and `ml-data/`, which you removed. The local commit guard went with `ml-data/`; `.gitignore` still ignores the folder.

This closes the 2026-11-01 decisions 3 (the APM pin) and 4 (`ml-data/`), and that day's "kept on purpose" list.

**Release pipeline repaired**

- **What went wrong:** the publish workflow had copied two release tags to the mirror as lightweight tags (bare pointers to the commit). The mirror then refused the real ones, so every publish run failed.
- **The fix:**
  - [Pull request #32](https://github.com/saulpatinojr/Proj-Agent_Packs/pull/32) fetches the real tags.
  - [Pull request #33](https://github.com/saulpatinojr/Proj-Agent_Packs/pull/33) moves every workflow to `actions/checkout` v7.0.1, which keeps tags annotated.
  - Both are merged.
- **The mirror:** with your approval, Claude replaced the two mirror tags once. All 25 tags now match.
- **Proof:** a [publish run](https://github.com/saulpatinojr/Proj-Agent_Packs/actions/runs/41525358873) on `main` passes again.

**Decisions waiting for you**

1. **Vendor documentation changed.** [Issue #11](https://github.com/saulpatinojr/Proj-Code_Workflow/issues/11): the weekly watch found that facts in `docs/client-locations.md` need re-checking.
2. **Code Conductor still pins APM 0.33.0.** Its decision D-077 says both repositories use the same version, so it is out of step until a pull request there moves it. That pull request regenerates Code Conductor's committed APM files and runs `apm audit`, APM's own consistency check.
3. **This repository's workflows still use `actions/checkout@v4` and `actions/setup-python@v5`.** GitHub now runs those on Node.js 24 and warns that the Node.js 20 they target is deprecated. Agent Packs moved to checkout v7.0.1, pinned by commit SHA.
4. Unchanged from 2026-11-01:
   - Antigravity.
   - The Copilot `customAgents` setting.
   - The four Code Workflow handoff gaps.

## 2026-11-01, for the next session

**Draw.io diagram packs: reviewed, fixed, waiting for you.**

- Three live generation tests ran in Claude Code (`aws-expert-designer`, `azure-expert-designer`, `google-cloud-architect`), each passing the strict checker and a visual check of its render. Two independent reviews and a pre-PR review followed.
- The shared skills' facts held against draw.io 32.6.9 and the official AWS, Microsoft and Google icon pages. The packs' own content did not: hand-typed AWS boundary colours, pack validators that passed legacy and misspelled icons, and a checker that passed icons drawn without their palette colour.
- The fixes are one draft pull request in Proj-Agent_Packs (AWS and Azure packs 1.5.0, Google Cloud 1.3.0). Merging it and creating the five release tags are yours; then `apm install -g` updates every client.

**What changed on this computer**

- `orchestration/generate.py` ran for real: the Claude Code orchestrator lists all 39 specialists again (it had 24), and the Codex and Copilot orchestrators now exist. A second run changes nothing.
- No pack was reinstalled: the installed copies already match their releases in Claude Code, Codex, Copilot and Kiro.

**Decisions waiting for you**

1. Antigravity: APM cannot install packs there at user scope. Leave it, or build it into the local setup script (plan step 6).
2. VS Code's Copilot chat shows the agents only with `github.copilot.chat.cli.customAgents.enabled` on; it is off.
3. APM 0.35.0: the Proj-Agent_Packs pin change never landed (issue #29 there).
4. `ml-data/` (git-ignored) holds the session's agent runs for evaluation; it is never committed. A local commit guard is ready in `ml-data/tools/client-data-guard`; installing it as a git hook needs you.

**Code Workflow gaps this session exposed (not fixed yet)**

Four workflows recorded the work with 18 specialist handoffs. Valid work showed as `blocked` until the agents corrected their records, for three reasons the controller and the handoff skill should handle:

1. **Status words.** Agents wrote their pack's completion word (`COMPLETE_VERIFIED`, `IMPLEMENTATION_PREPARED_NOT_VERIFIED`) into `status`, which accepts only `completed`, `partial`, `blocked`, `failed_retryable` or `failed_terminal`. The handoff skill should say so, and the agents now record the pack word in a separate `contract_status` field.
2. **Evidence outside the workflow root.** When the workflow runs in one repository and changes another (here Code Workflow and Proj-Agent_Packs), agents cite worktree or scratchpad paths, which the controller rightly rejects. The skill should tell agents to copy evidence into the workflow's `artifacts/` folder.
3. **YAML block text.** The handoff parser does not read folded or literal block scalars (`>-`, `|`); it stores the literal `>-` as the summary, without an error. Eight handoffs used them. The fix is in the parser, with a test, not in the agents.
4. **Which folder paths are relative to.** Evidence paths must be relative to the repository root (`.agentic/workflows/<id>/artifacts/...`). Agents told "relative to the workflow root" wrote paths relative to the workflow folder (`artifacts/...`), and the controller found none of their files. The skill should name the base with an example, or the controller should also try the workflow folder.

**Kept on purpose**

- The Proj-Agent_Packs worktrees `Proj-Agent_Packs-wt-*` and their local branches, until the pull request merges.

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
- Codex and Copilot have no Code Workflow orchestrator on this computer: the old installer was only ever run for Claude Code here. Their templates come next.
