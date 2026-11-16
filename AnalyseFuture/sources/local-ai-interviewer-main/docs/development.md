# Developer guide

How to get a working development setup, run every check CI runs, and find where to make a change. For the rules a pull request must
follow, see [CONTRIBUTING.md](../CONTRIBUTING.md). For how the pieces fit together, see [architecture.md](architecture.md).

## Prerequisites

| Tool | Needed for | Notes |
|---|---|---|
| Python 3.10 or newer | backend, launcher | CI tests 3.10 and 3.12. |
| Node.js 22.12+ (20.19+ is enough to run the app, not the frontend tests) | frontend | CI uses Node 22. Linux distribution packages are often too old: use the LTS from nodejs.org. |
| Git | | |
| [Ollama](https://ollama.com/download) | real interviews with a local model | Optional for development: the backend tests mock the model, and cloud mode needs no local Ollama. |
| Google Chrome | the optional real-browser e2e scripts only | |
| [uv](https://docs.astral.sh/uv/) | | Optional. If it is on your PATH the launcher uses it to create the virtualenv and install packages; otherwise it uses `python -m venv` and `pip`. |

Install hints per system are printed by `./check.sh` (`check.bat` on Windows). Windows and Linux are covered by CI but have not been
run on real machines by the maintainer (see [README section 2](../README.md#2-supported-platforms)); corrections to this guide from
those systems are welcome.

## First run

```bash
git clone https://github.com/Yuvakunaal/local-ai-interviewer.git
cd local-ai-interviewer
./check.sh            # Windows: check.bat   (read-only: reports what is missing)
./setup-models.sh     # Windows: setup-models.bat  (optional: downloads the local model after asking)
./start.sh --open     # Windows: start.bat --open
```

`./start.sh` runs `scripts/run.sh`, which finds Python 3.10+ and runs `scripts/manage.py start`. On the first run the launcher:

1. creates the virtualenv at `backend/.venv` and installs `backend/requirements.txt` (with `uv` if present, otherwise `pip`);
2. runs `npm install` in `frontend/` if `frontend/node_modules` does not exist;
3. builds the frontend (`npm run build`) when `frontend/dist` is missing or older than the sources;
4. starts Ollama if it is installed but not running (set `OLLAMA_AUTOSTART=0` to prevent that);
5. starts the backend with uvicorn in the background, logging to `logs/backend.log`.

The app is then at <http://localhost:3000>. Stop it with `./stop.sh` (`stop.bat`); `./stop.sh --unload` also frees the model's memory.
All settings are environment variables, optionally in a `.env` file copied from [.env.example](../.env.example).

### Development mode

```bash
./start.sh --dev
```

This starts the backend on `127.0.0.1:8000` and the Vite dev server on `127.0.0.1:3000` (hot reload for the frontend), with Vite
proxying `/api` to the backend. It skips the production frontend build. Logs go to `logs/backend.log` and `logs/frontend.log`.

The backend is started **without** auto-reload. After changing Python code run `./stop.sh && ./start.sh --dev`. Frontend changes
reload by themselves.

### Where things live on disk

| Path | What |
|---|---|
| `backend/.venv/` | Python virtualenv. Binaries are in `bin/` (macOS, Linux) or `Scripts\` (Windows). |
| `frontend/node_modules/`, `frontend/dist/` | Frontend dependencies and the production build. |
| `data/` | SQLite database, resume PDFs, audio cache, backups. Override with `DATA_DIR`. Git-ignored. |
| `logs/` | `backend.log`, `frontend.log` (dev mode), `ollama.log`, `frontend-build.log`. Git-ignored. |
| `.run/` | PID files used by `stop`. Git-ignored. |

## Running the checks

Run these from the repository root unless stated otherwise. On Windows replace `backend/.venv/bin/` with `backend\.venv\Scripts\`.

### Install the development tools once

The virtualenv created by `start.sh` has the runtime requirements only. Add the test and lint tools:

```bash
# if you have uv installed (the launcher then created the venv without pip):
uv pip install --python backend/.venv/bin/python -r backend/requirements-dev.txt
# otherwise:
backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt
```

`requirements-dev.txt` adds pytest, pypdf, pytest-cov, pip-audit and a pinned `ruff` (the same version CI uses).

### Backend

```bash
backend/.venv/bin/python -m pytest backend                                   # everything (mocked model, no downloads)
backend/.venv/bin/python -m pytest backend/tests/test_evaluator.py -q        # one file
backend/.venv/bin/python -m pytest backend -k "followup" -q                  # by name
backend/.venv/bin/python -m pytest backend -q --cov=backend/app --cov-report=term-missing:skip-covered   # coverage
backend/.venv/bin/ruff check .                                               # lint (rules in ruff.toml)
```

Total line coverage was **94 %** on 2026-11-15 on this branch. Tests mock Ollama with `httpx.MockTransport` and a fake cloud server
(`backend/tests/fakecloud.py`), so no model is downloaded and nothing needs a GPU. Tests that need the real models are marked
`integration` (see `backend/pytest.ini`), live in `backend/tests/integration/` and are described below.

`ruff.toml` selects bug-finding rules only (pyflakes, bugbear, syntax errors); formatting is not enforced by a tool, so match the
style of the file you are editing.

### Documentation

```bash
python3 scripts/check_docs.py        # every relative Markdown link, image and #anchor must resolve
```

It is offline: external URLs are not fetched (see [releasing.md](maintainers/releasing.md) for the manual check before a release).
`backend/tests/test_repository.py` also runs it, along with checks that every setting in `config.py` is documented in `.env.example`,
that backend and frontend versions match, and that workflow actions are pinned to commit SHAs.

### Frontend

```bash
cd frontend
npm ci                  # exact versions from package-lock.json
npm run lint            # ESLint, zero warnings allowed
npm run typecheck       # tsc --noEmit
npm test                # vitest
npm run build           # type check + production build into frontend/dist
```

### Everything CI runs

`.github/workflows/ci.yml` runs: ruff, `check_docs.py` and ESLint (Ubuntu); backend tests with coverage on Ubuntu, macOS and Windows
(Python 3.12, plus 3.10 on Ubuntu); frontend typecheck, tests and build on all three systems; and a launcher smoke test
(`python scripts/manage.py check`) on all three. `.github/workflows/security.yml` adds dependency scanning and CodeQL (see
[SECURITY.md](../SECURITY.md)).

## Optional: real-browser end-to-end scripts

`frontend/e2e/*.mjs` drive your installed Google Chrome with puppeteer-core. Each script starts **its own backend on port 3100 with a
throw-away data directory**, so your real interviews are never touched. Examples:

```bash
cd frontend
node e2e/basics.mjs        # smoke test, no model needed
node e2e/ui-audit.mjs      # every page in light and dark: screenshots, text contrast, overflow
node e2e/resumes.mjs       # resumes with a fake local model
node e2e/cloud.mjs         # cloud mode against a fake cloud server (no network, no credits)
node e2e/full-flow.mjs     # a full interview with the REAL local models
```

`npm run e2e`, `e2e:full`, `e2e:mic` and `e2e:voices` are shortcuts for four of them. The README's
[Tests section](../README.md#12-tests) lists them all. CI does not run these scripts.

## Optional: real-model integration tests

With Ollama running and `qwen3.5:4b` installed:

```bash
RUN_INTEGRATION=1 backend/.venv/bin/python -m pytest -m integration -s backend/tests/integration
```

These talk to the real local models and are not part of CI. If you change the grading prompt, run them and describe what you saw in
the pull request: the quality of the 2.0 grading with a real model has not been measured systematically (see [ROADMAP](../ROADMAP.md)).

## Debugging

- **Logs:** `logs/backend.log` (ids, sizes and timings; never answers, resume text or API keys). In dev mode also `logs/frontend.log`.
  Run `tail -f logs/backend.log` while you click around.
- **API explorer:** set `API_DOCS=1` in `.env` and restart; then <http://localhost:3000/api/docs> is the interactive OpenAPI UI (in dev
  mode the proxy serves it on :3000; the backend itself is on :8000). It is off by default because that page loads Swagger UI's
  JavaScript and CSS from a public CDN, which would break the app's "only localhost" promise. The raw schema at `/api/openapi.json`
  is always available and fully local.
- **Health:** `curl -s localhost:3000/api/health` reports the bind address, Ollama and model status, voice and speech-to-text status, and memory.
- **Errors** from the API have the shape `{"error": {"code": "...", "message": "..."}}` (see `backend/app/errors.py`).
- **Run the backend in the foreground** to see everything: stop the launcher's copy, then from `backend/` run
  `.venv/bin/python -m uvicorn app.main:app_factory --factory --host 127.0.0.1 --port 8000 --reload`. This is how the launcher
  starts it, plus `--reload`.
- **Inspect the database:** `sqlite3 data/interviewer.sqlite3` (or any SQLite browser) while the app is stopped, or read-only while it
  runs. Do not edit rows by hand.
- **A fresh start:** point `DATA_DIR` at an empty folder to try the first-run experience without touching your data.
- **Browser:** Chrome DevTools, Network tab. In local mode every request should go to `localhost`.

## Where do I change...?

| I want to change... | Start here | Also update |
|---|---|---|
| The grading prompt or output schema | `backend/app/services/prompts.py` (bump `PROMPT_VERSION`) | `docs/evaluation.md`, tests in `test_evaluator.py`, `test_grading_fairness.py` |
| Scoring weights, evaluation profiles, profile detection | `backend/app/services/eval_profiles.py` | `docs/evaluation.md`, `test_eval_profiles.py` |
| Grounding and consistency rules | `backend/app/services/grounding.py` | `docs/evaluation.md`, `test_grounding.py` |
| Follow-up policy (when and how many) | `decide_followup()` in `backend/app/services/evaluator.py`; adaptive follow-ups in `services/adaptive.py` (`choose_followup`) | `docs/evaluation.md`, `docs/adaptive-interviews.md` |
| The adaptive engine (levels, strategies, early end) | `backend/app/services/adaptive.py` (pure functions) | `docs/adaptive-interviews.md`, `test_adaptive_engine.py`, ADR 0003 |
| The interview state machine | `backend/app/services/interviews.py` | `test_interview_flow.py`, `test_state_machine_guards.py` |
| Resume reading and organising | `backend/app/services/resume_extract.py`, `resume_profile.py`, `resumes.py` | `test_resumes.py` |
| The candidate profile | `backend/app/services/candidate_profile.py` | `docs/resume-intelligence.md`, `test_candidate_profile.py` |
| The offline resume-question catalogue | `backend/app/services/tech_implications.py` | `docs/resume-intelligence.md`, `test_resume_questions.py` |
| AI-written resume questions | `backend/app/services/resume_questions.py`, `prompts.py` | `test_resume_questions.py` |
| Report analytics and exports (Markdown, JSON, PDF, redaction) | `backend/app/services/reports.py`, `report_pdf.py`, `stats.py` | `test_report_pdf.py`, `test_stats.py`, `test_intelligence_flow.py` |
| Local vs cloud routing, budgets | `backend/app/services/gateway.py`, `ai_config.py`, `cloud.py`, `pricing.py` | `test_cloud_mode.py`, `test_ai_config.py` |
| A new setting | `Settings` and `Settings.from_env()` in `backend/app/config.py` | `.env.example` (documented there, checked by `test_repository.py`), README if user-visible |
| A new API route | A router in `backend/app/routers/`, request/response models in `backend/app/schemas.py`; new routers are registered in `backend/app/main.py` | An API test; the frontend client `frontend/src/api.ts` and `types.ts` |
| A new page or component | `frontend/src/pages/` (pages are lazy-loaded and routed by URL hash in `frontend/src/App.tsx`), `frontend/src/components/` | A Chrome e2e script or `qa-sweep.mjs` if it adds navigation |
| Colours, light and dark themes | CSS variables in `frontend/src/styles.css` and `theme-dark.css` | Run `node e2e/ui-audit.mjs` for contrast |
| The launcher | `scripts/manage.py` (standard library only) and the `.sh` / `.bat` wrappers | `backend/tests/test_launcher.py` |
| The database schema | `backend/app/db.py` (see below) | An upgrade test |

## Database migrations

SQLite is opened with one short-lived connection per unit of work and explicit transactions (`backend/app/db.py`). The schema version
is stored in `PRAGMA user_version` and is the constant `SCHEMA_VERSION` (currently 6).

Rules:

1. **Additive only.** Add tables, columns (with defaults) and indexes. Never drop, rename or rewrite existing user rows or columns.
2. **Bump `SCHEMA_VERSION`** and add a step to `Database._migrate()` that upgrades from the previous version in place. A brand-new
   database is created from the full schema; an existing one is upgraded step by step.
3. **Add an upgrade test**: build a database at the previous version, open it with the new code, and assert that old rows are intact
   and the new structure works (see `test_v5_database_upgrades_to_v6_and_old_interviews_still_load` in `backend/tests/test_adaptive_flow.py` for the pattern).
4. A database whose version is newer than the app refuses to open; do not weaken that.
5. A change that cannot be done additively is a breaking change (see [releasing.md](maintainers/releasing.md)) and needs an ADR.

## Troubleshooting your setup

- `Port 3000 is already in use`: another program holds it; stop it or set `APP_PORT` in `.env`.
- `No module named venv` on Debian/Ubuntu: `sudo apt install python3-venv`.
- Backend dependencies look out of date: delete `backend/.venv` and run `./start.sh` again.
- Ollama is not needed for the test suites. It is needed for `full-flow.mjs`, the integration tests and real interviews in local mode.
