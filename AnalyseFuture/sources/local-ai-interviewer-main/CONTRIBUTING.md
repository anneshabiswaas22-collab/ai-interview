# Contributing

Thanks for helping. This is a local-first app: please keep it that way (no telemetry, no CDNs, no silent network calls).

By taking part you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md). Looking for help rather than contributing? See
[SUPPORT.md](SUPPORT.md). Security problems go through [SECURITY.md](SECURITY.md), not public issues.

The full setup, debugging tips and a "Where do I change...?" table are in the [developer guide](docs/development.md); how the pieces fit
together is in [docs/architecture.md](docs/architecture.md).

## Setup

```bash
./start.sh --dev            # backend on :8000 + Vite on :3000 (hot reload for the frontend; restart to pick up Python changes)
```

Windows: `start.bat --dev`. In the commands below use `backend\.venv\Scripts\python` instead of `backend/.venv/bin/python`, and
`python` instead of `python3`. For the optional real-model tests set the variable first: `set RUN_INTEGRATION=1` (Command Prompt) or
`$env:RUN_INTEGRATION = "1"` (PowerShell).

Backend: Python >= 3.10, dependencies in `backend/requirements*.txt` (a virtualenv is created in `backend/.venv` by `start.sh`).
Frontend: Node 22.12+ for development (the frontend tests need it; running the app needs 20.19+ or 22.12+), then `cd frontend && npm ci`.

## Before you open a pull request

Run what CI runs (details and Windows paths in [docs/development.md](docs/development.md#running-the-checks)). Install the dev tools
once: `backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt` (with `uv`: `uv pip install --python backend/.venv/bin/python -r backend/requirements-dev.txt`).

```bash
backend/.venv/bin/ruff check .                      # Python lint (rules in ruff.toml)
python3 scripts/check_docs.py                       # Markdown links, images and anchors
backend/.venv/bin/python -m pytest backend          # mocked model, no downloads (CI: macOS, Windows, Linux)
cd frontend
npm run lint                                        # ESLint, no warnings
npm run typecheck
npm test
npm run build
```

Optional: the real-Chrome e2e scripts in `frontend/e2e/` and the real-model tests (`RUN_INTEGRATION=1 ... -m integration`).

## Ground rules

- **Never weaken or delete a test to make CI pass.** If behaviour changes on purpose, update the test and explain why in the PR.
- The model never decides a score, a limit or a state transition: put policy in code and test it (see `docs/adr/`).
- Database changes are additive migrations in `backend/app/db.py` with an upgrade test from the previous version; never rewrite user rows.
- Don't change which inference models users depend on; add new ones only as opt-in.
- Treat any user-supplied text (answers, resumes, question imports) as untrusted in prompts.
- Keep UI changes token-driven (CSS variables) so light and dark themes both work; no heavy animation.
- Architecture decisions that change these rules get an ADR in `docs/adr/`.
- Update `CHANGELOG.md` under *Unreleased*.
- Never commit secrets, `.env`, database files, logs or personal data (a test checks for this).

## Branches and pull requests

1. Fork the repository (or create a branch if you have access) and branch from `main`: `fix/short-description` or
   `feature/short-description`.
2. Keep a pull request focused on one thing. Draft pull requests are welcome for early feedback.
3. Fill in the pull request template: what and why, how you tested, any breaking change or upgrade note.
4. CI and the security workflow must pass. Review comments are about the change, not the person; please reply to or resolve each.
5. Changes are merged into `main` by the maintainer.

### Commit messages

- Short imperative subject line (about 70 characters): "Fix follow-up count after retry", not "Fixed" or "Fixes".
- Use the body to explain **why**, not just what; the diff already shows what. Mention trade-offs and anything surprising.
- Reference issues with `Fixes #123` in the pull request description or commit body.
- A [Developer Certificate of Origin](https://developercertificate.org/) sign-off (`Signed-off-by`) is **not** required. By submitting a
  contribution you agree that it is licensed under the project's [MIT license](LICENSE).

## Picking something to work on

- Look for issues labelled **good first issue** (small, well described) or **help wanted** (a pull request would be welcome). Comment
  to say you are taking one so work is not duplicated.
- [ROADMAP.md](ROADMAP.md) lists intentions; items marked "contributors welcome" are good starting points. Verifying the app on a real
  Windows or Linux machine and reporting what you find is a valuable contribution even without code.
- For a larger change, open an issue or discussion first so the approach can be agreed before you invest time.

## Labels

Defined in `.github/labels.yml`:

| Label | Meaning |
|---|---|
| `bug`, `enhancement`, `documentation`, `question` | Type of issue. Questions are better asked in Discussions (if enabled). |
| `good first issue` | Small, well described, suitable for newcomers. |
| `help wanted` | The maintainer would welcome a pull request. |
| `needs reproduction` | Cannot be acted on until it can be reproduced; more details requested. |
| `frontend`, `backend`, `evaluation`, `platform`, `testing`, `ci` | Area of the code (`evaluation` = grading, profiles, follow-ups, reports; `platform` = launcher and OS specifics). |
| `security` | Security or privacy issue. Report vulnerabilities privately, never with this label in public. |
| `performance` | Speed, memory, model load time. |
| `breaking change` | Requires users to change something when upgrading; listed first in release notes. |
| `dependencies` | Dependency updates (Dependabot). |
