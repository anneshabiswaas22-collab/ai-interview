# Repository settings checklist

Some settings can only be changed by the repository owner in the GitHub web interface; they cannot be set from files in the
repository. This is the checklist for the owner of `Yuvakunaal/local-ai-interviewer`. Menu names are those on github.com and may
move slightly over time.

Open the repository, then **Settings** (the tab at the right of the repository's top menu).

## About box (description, topics, social preview)

- [ ] **Description and website.** On the repository home page click the gear icon next to **About**. Suggested description (under
  350 characters):

  > Local-first mock-interview app. Practise technical and behavioural interviews with a local Ollama model: adaptive questions, evidence-based grading, resume-based questions and reports. Runs on your computer; optional cloud mode and voice.

  Leave the website field empty unless you have one.
- [ ] **Topics** (up to 20). In the same dialog add, for example: `ollama`, `local-first`, `mock-interview`, `interview-preparation`,
  `fastapi`, `react`, `typescript`, `sqlite`, `privacy`, `offline`, `llm`, `speech-to-text`, `whisper`, `python`, `vite`,
  `self-hosted`.
- [ ] **Social preview image.** *Settings, General, Social preview, Edit, Upload an image.* The image to upload is
  `docs/assets/social-preview.png` (once it exists in the repository; GitHub recommends 1280 x 640 pixels, under 1 MB).

## Security

- [ ] **Private vulnerability reporting.** *Settings, Advanced Security* (called *Code security* on some accounts), find **Private
  vulnerability reporting**, click **Enable**. [SECURITY.md](../../SECURITY.md) and the issue chooser both point reporters to it.
- [ ] **Dependabot alerts.** Same page: **Dependabot alerts**, click **Enable**.
- [ ] **Dependabot security updates.** Same page: **Dependabot security updates**, click **Enable**. Version updates are already
  configured by `.github/dependabot.yml` (weekly pip and npm, monthly GitHub Actions, grouped).
- [ ] **CodeQL: do not enable "default setup".** The workflow `.github/workflows/security.yml` already runs CodeQL (Python and
  JavaScript/TypeScript, `security-extended` queries). Enabling the default setup as well would scan everything twice. Leave
  *Code scanning* on the workflow (advanced) setup.
- [ ] **Secret scanning and push protection.** On the same page enable **Secret scanning** and **Push protection** (free for public
  repositories). This helps because the optional cloud API key is the one secret contributors might paste by accident.

## Branch protection for `main`

*Settings, Branches, Add branch ruleset* (or *Add classic branch protection rule*), target branch `main`:

- [ ] Require a pull request before merging (one approval is optional for a single maintainer; if you require one you cannot approve
  your own PRs, so leave it at zero unless you have a second reviewer).
- [ ] Require status checks to pass before merging, and require branches to be up to date. Add these checks (job names from the
  workflows; they appear in the picker after they have run once):
  - From `ci.yml`: `Lint, docs and repository checks`
  - `Backend tests (ubuntu-latest, Python 3.12)`, `Backend tests (macos-latest, Python 3.12)`, `Backend tests (windows-latest, Python 3.12)`,
    `Backend tests (ubuntu-latest, Python 3.10)`
  - `Frontend typecheck, tests and build (ubuntu-latest)`, `... (macos-latest)`, `... (windows-latest)`
  - `Launcher smoke test (ubuntu-latest)`, `... (macos-latest)`, `... (windows-latest)`
  - From `security.yml`: `Dependency review (new dependencies in this PR)`, `Python dependencies (pip-audit)`,
    `Frontend dependencies (npm audit)`, `CodeQL (python)`, `CodeQL (javascript-typescript)`

  Consider requiring only the Ubuntu jobs plus the Lint job at first and adding the others once you see they are stable. The
  `npm audit` and `pip-audit` jobs depend on advisories published after a change is written, so they can fail on an unrelated PR;
  decide whether they should block merging.
- [ ] Block force pushes and deletion of `main`.
- [ ] Optional: require conversation resolution; require linear history if you prefer squash or rebase merges.
- [ ] **Merge button.** *Settings, General, Pull Requests*: allow squash merging (default message: pull request title and
  description), and automatically delete head branches.

## Labels

- [ ] Run the **Sync labels** workflow once: *Actions, Sync labels, Run workflow*. It creates or updates the labels in
  `.github/labels.yml` and never deletes others. Re-run it after editing that file. The issue templates, Dependabot and the release
  notes categories use these labels. **Do this right after merging:** Dependabot opens its first pull requests on the next Monday and
  can only attach labels that exist (today the repository has only GitHub's default labels).

## Actions

- [ ] *Settings, Actions, General*: set **Workflow permissions** to *Read repository contents* (each workflow also declares its own
  least-privilege permissions). Under *Fork pull request workflows*, keep the default of requiring approval for first-time
  contributors.
- [ ] The release workflow needs to create releases with the built-in token; this works with its own `contents: write` declaration, so
  no personal access token is needed.

## Discussions (recommended)

- [ ] *Settings, General, Features*, tick **Discussions**. Then *Discussions, edit categories* and keep or create:
  **Q&A** (answerable questions), **Ideas**, **Show and tell**, **Announcements** (maintainer-only posting).

Why: usage questions, half-formed ideas and "here is what I built with it" posts do not belong in the issue tracker, which is for
work that can be closed. Separating them keeps the issue list actionable, lets answers be marked and found later, and gives
newcomers a lower-pressure place to ask. [SUPPORT.md](../../SUPPORT.md) mentions Discussions "if enabled", so nothing breaks if you
decide against it. The issue chooser deliberately has **no** Discussions link yet (it would 404); after enabling Discussions, add this
entry under `contact_links` in `.github/ISSUE_TEMPLATE/config.yml`:

```yaml
  - name: Questions and ideas
    url: https://github.com/Yuvakunaal/local-ai-interviewer/discussions
    about: Ask how-to questions or float an idea.
```

## Projects and good first issues

- [ ] **One simple board.** *Projects, New project, Board*, with the columns *Ideas, Ready, In progress, Done*. Add issues
  automatically (project *Workflows*). One board is enough for a single-maintainer project; resist adding more fields.
- [ ] **Good first issues.** Curate a few and label them `good first issue` (and `help wanted` for larger ones). A good one has: a
  clear problem statement, the files to look at (the "Where do I change...?" table in [development.md](../development.md) helps),
  how to test it, and a rough size. [ROADMAP.md](../../ROADMAP.md) marks items suitable for contributors. GitHub lists issues with
  this label on the repository's `contribute` page, so it is worth keeping 3 to 5 current.

## Community profile

- [ ] Open `https://github.com/Yuvakunaal/local-ai-interviewer/community` and confirm every item is green (description, README, code
  of conduct, contributing, license, security policy, issue templates, pull request template).
