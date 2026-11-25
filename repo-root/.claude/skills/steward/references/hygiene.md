# Mode: hygiene

Audit the repository's housekeeping. Run every check; record each result in the findings table.

## Checks

| Area | How to check | Fix on the branch? |
|---|---|---|
| Stale branches | `git fetch --prune` then `git for-each-ref --sort=committerdate --format='%(committerdate:short) %(refname:short)' refs/remotes/origin`; flag branches merged into the default branch or idle > 90 days | No. List them; deletion needs owner approval |
| Stale issues / PRs | `gh issue list --state open --json number,title,updatedAt` and `gh pr list --state open --json number,title,isDraft,updatedAt`; flag items idle > 60 days | No. List them; closing or labeling needs approval |
| GitHub Actions versions | Grep `.github/workflows/*.yml` for `uses:`. Flag deprecated majors (for example `actions/checkout@v3`, `actions/setup-python@v4`) and third-party actions not pinned to a full commit SHA | Yes: bump first-party majors after checking the action's release notes; SHA-pin third-party actions |
| Workflow permissions | Flag workflows with no top-level `permissions:` block or with `write-all` | Yes: add least-privilege `permissions:` (default `contents: read`) |
| Runtimes | Flag end-of-life language versions in CI matrices, `.python-version`, `.nvmrc`, `engines`, `required_version`, provider constraints | Yes for patch/minor; ask for major |
| Dependencies | Use the ecosystem's own tool (`pip list --outdated`, `npm outdated`, `terraform init -upgrade` in a scratch copy, `dotnet list package --outdated`). Flag known-vulnerable versions first | Yes for patch/minor with passing tests; ask for major |
| Ownership and docs | Check for `README.md`, `LICENSE`, `.github/CODEOWNERS`, `SECURITY.md`, `CONTRIBUTING.md`, and `docs/adr/` (or the repo's ADR folder) when architecture decisions exist | Yes: add missing CODEOWNERS/SECURITY.md stubs using owners the user names; never invent owners |
| Secrets exposure | Scan tracked files for key patterns and committed `.env`, `*.tfstate`, `*.pem`, `*.pfx`. Report the path only, never the value | No. Report as `high`; rotation is the owner's call |
| Ignore rules | Confirm `.gitignore` covers build output, `.terraform/`, `*.tfstate*`, `.env`, `.agentic/` runtime folders | Yes |
| Convention drift | Compare against the rules in `CLAUDE.md`/`AGENTS.md` (naming, folder layout, required files) | Yes when the rule is explicit |

## Done when

Every row above has a result in the findings table, safe fixes are committed one per concern, and the repository's checks were run after the last commit.
