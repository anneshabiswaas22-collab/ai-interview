# Releasing

How versions are numbered and how a release is made. There are no git tags or published releases yet; the first release will follow
this procedure. Releases are automated by [`.github/workflows/release.yml`](../../.github/workflows/release.yml). Nothing is deployed:
users run the app from source, so a release is a tag, a source archive and release notes.

## Versioning policy

The project follows [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`).

**MAJOR (breaking)** — a user or integration must change something when upgrading:

- A change to the HTTP API contract under `/api` that existing clients would break on (removed or renamed route, field or error code,
  changed meaning of a field). The bundled frontend is updated together with the backend, so this matters for people who script
  against the API or export files.
- A database schema change that cannot be applied automatically and non-destructively. Additive migrations (new tables or columns
  with defaults, [rules here](../development.md#database-migrations)) are **not** breaking.
- A removed or renamed setting (environment variable) or a changed default that alters behaviour users rely on.
- A changed default model (`LLM_MODEL`, `TTS_MODEL`, `STT_MODEL`), because it changes download size, memory use and results.
- A change that makes the app require a newer Python or Node major than before.

**MINOR** — new backwards-compatible features: new endpoints or optional fields, new settings with safe defaults, new pages, new
evaluation profiles, additive migrations.

**PATCH** — bug fixes, documentation, internal changes and dependency updates that change no behaviour.

Grading prompt or scoring changes that shift scores are called out in the changelog even when they are not breaking, because users
compare reports over time.

## The single version source

The version is written in two places that must agree:

- `backend/app/__init__.py`: `__version__ = "X.Y.Z"`
- `frontend/package.json`: `"version": "X.Y.Z"` (also update `frontend/package-lock.json` by running `npm install --package-lock-only`
  in `frontend/`)

`backend/tests/test_repository.py` fails if they differ or if the value is not of the form `X.Y.Z` optionally followed by
`-rc.1`/`-dev.1`/`-a.1`/`-b.1` style suffix. `release.yml` additionally checks that the tag equals both.

## CHANGELOG conventions

[CHANGELOG.md](../../CHANGELOG.md) follows [Keep a Changelog](https://keepachangelog.com/). Contributors add entries under
`## [Unreleased]` in groups (Added, Changed, Fixed, Removed, Security). At release time the maintainer renames that section.

**Required:** a heading that starts exactly with `## [X.Y.Z]` followed by ` - YYYY-MM-DD`, for example `## [2.0.0] - 2026-12-01`.
`release.yml` extracts everything between that heading and the next `## [` heading as the release notes and fails if the section is
missing or empty. Keep an empty `## [Unreleased]` heading above it for the next cycle. For a pre-release use the full version in the
heading, for example `## [2.0.0-rc.1] - 2026-11-20`.

## Release procedure

1. **Decide the version** using the policy above. Look at the merged pull requests since the last release
   (`git log --oneline <last-tag>..main`, or the PR labels, especially `breaking change`).
2. **Create a branch:** `git switch -c release/X.Y.Z` from an up-to-date `main`.
3. **Bump the version** in `backend/app/__init__.py` and `frontend/package.json` (and the lock file, see above).
4. **Update the changelog:** rename `## [Unreleased]` content into `## [X.Y.Z] - YYYY-MM-DD`, add a fresh empty `## [Unreleased]`,
   and check that user-visible changes, breaking changes and upgrade steps are listed.
5. **Check links** (see below) and run the full local checks from [development.md](../development.md#running-the-checks).
6. **Open a pull request** into `main`. Wait for the CI and Security workflows to pass, then merge.
7. **Tag the merge commit** (annotated):
   ```bash
   git switch main && git pull
   git tag -a vX.Y.Z -m "Local AI Interviewer X.Y.Z"
   git push origin vX.Y.Z
   ```
8. **Watch the Release workflow** (Actions tab). It verifies tag, backend and frontend versions agree; runs backend tests and the
   frontend lint, typecheck, tests and build; extracts the changelog section; builds a source `.zip` with `git archive`; and creates the
   GitHub release, marking it as a pre-release if the tag contains a `-`.
9. **Review the published release** on GitHub: notes read well, the archive is attached. Add the upgrade steps and breaking changes
   (template below) if the changelog section does not already contain them. Edit the release rather than re-tagging.
10. Optionally post an announcement using [the templates](../community/templates.md).

If the workflow fails before creating the release, fix the cause on `main`, delete the tag locally and on GitHub
(`git tag -d vX.Y.Z && git push origin :refs/tags/vX.Y.Z`) and tag again. Never move a tag that has a published release; ship a new
patch version instead.

## Pre-releases

Use a hyphenated suffix: `X.Y.Z-rc.1`, `X.Y.Z-rc.2`. The tag pattern in `release.yml` (`v[0-9]+.[0-9]+.[0-9]+*`) accepts them, and
the release is published as a pre-release. The version in `__init__.py` and `package.json` must be the same suffixed string, and the
changelog needs a `## [X.Y.Z-rc.1]` section. The final release is then a normal `X.Y.Z`.

## Release notes template

```markdown
## Highlights
- One or two sentences on what matters most to users.

## Upgrade steps
1. `git pull` (or download the source archive), stop the app (`./stop.sh`), and start it again with `./start.sh`. The frontend is rebuilt
   automatically. If `frontend/package.json` changed, also run `npm ci` in `frontend/`; if `backend/requirements.txt` changed and the app
   does not start, delete `backend/.venv` and start again.
2. Your data folder (`data/`) is upgraded in place on first start. To be careful, download a backup first (Settings, Backup card, "Download a backup").
3. Anything else the user must do (new settings, models to download).

## Breaking changes
- None.   (Otherwise: what changed, who is affected, what to do instead.)

## Changes
See the full list in [CHANGELOG.md](https://github.com/Yuvakunaal/local-ai-interviewer/blob/main/CHANGELOG.md).

## Known limitations
- Windows and Linux are covered by CI but not verified on real machines; cloud mode is verified against a fake server only.
  (Edit to match README section 11 at the time.)
```

## Checking external links before a release

`python3 scripts/check_docs.py` verifies relative links, images and anchors only; it does not fetch external URLs. Before a release,
open the external links in the README and docs by hand (or with a link checker you trust, run locally) and fix anything that has
moved. Pay particular attention to the Ollama, Contributor Covenant and GitHub URLs, and to the security advisory link in
`.github/ISSUE_TEMPLATE/config.yml`.
