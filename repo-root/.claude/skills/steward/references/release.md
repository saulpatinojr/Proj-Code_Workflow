# Mode: release

Prepare a release for a person to publish. You stop at a draft pull request; tagging and publishing are the owner's.

## Steps

1. **Find the last release.** `git describe --tags --abbrev=0` (fallback: `gh release list --limit 1`). If there is none, the range is the whole history.
2. **Collect changes.** `git log <last-tag>..HEAD --no-merges --format='%h %s'` and merged PRs with `gh pr list --state merged --search "merged:>=<last-tag-date>" --json number,title,labels`.
3. **Pick the version** with Semantic Versioning, unless the repository documents another scheme:
   - any breaking change (`!` in a Conventional Commit, `BREAKING CHANGE:` footer, or a `breaking` label) → major; while the version is `0.x`, breaking → minor;
   - any `feat` → minor;
   - otherwise → patch.
   State the rule that decided it.
4. **Update the changelog.** In `CHANGELOG.md`, turn the unreleased section into `## <version> (<yyyy-mm-dd>)` under `Added` / `Changed` / `Fixed` / `Removed` / `Security`, written for users, each entry linking its PR. Open a fresh empty unreleased section above it.
5. **Bump version strings** wherever the repository declares them (for example `pyproject.toml`, `package.json`, `__version__`, a `--version` constant, module `version` fields). Grep for the old version to catch every copy.
6. **Draft release notes** in `.github/release-notes/<version>.md`: a two-sentence summary, highlights, upgrade notes for any breaking change, and contributors.
7. **Verify** with the repository's full test suite and CI-equivalent commands.
8. **Open a draft PR** titled `release: <version>`. In the PR body, list the exact commands the owner runs after merging, for example:

   ```bash
   git tag -a v<version> -m "v<version>" && git push origin v<version>
   gh release create v<version> --notes-file .github/release-notes/<version>.md
   ```

## Never

- Run `git tag`, push tags, run `gh release create`, or publish to a package registry.
- Merge the release PR.

## Done when

Changelog, version strings, and release notes agree on one version; tests pass; the draft PR lists the owner's publish commands.
