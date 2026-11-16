# Changelog

All notable changes to this project. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[Semantic Versioning](https://semver.org/) as defined for this app in [docs/maintainers/releasing.md](docs/maintainers/releasing.md).
No version has been tagged or released on GitHub yet.

## [Unreleased]

Planned as 2.0.0 (database schema v6; scores of categorised questions change, see *Changed*).

### Interface
- Setup: one-click presets (Quick practice, Full mock, Resume round) that fill the settings below; the voice picker shows the chosen
  voice and opens the full list only on "Change voice" (names no longer cut off).
- Report: organised into tabs (Overview, Questions, Skills & progress, Adaptive); "Overall feedback" and "Insights" merged into one
  card; the selected tab survives a reload; on phones every tab stays visible.
- Home: a "Next step" card (continue the interview in progress, practise your weakest topics, or start the first interview).
- Interview: more space around "Why this question"; "Time left" turns amber in the last five minutes.
- Candidate profile: skills grouped by confidence (high open, medium and listed-only folded).

### Project infrastructure
- CI rebuilt: lint/docs job, backend tests on macOS/Windows/Linux (Python 3.12) plus Ubuntu on Python 3.10, frontend checks on all three
  systems, launcher smoke test; actions pinned to commit SHAs, least-privilege permissions, cancelled duplicate runs, dependency caching.
- Security workflow: dependency review on pull requests, pip-audit, npm audit, CodeQL (`security-extended`); weekly schedule. Dependabot
  for pip, npm and GitHub Actions.
- Lint: ruff (bug-finding rules only) and ESLint (TypeScript + React hook rules); optional pre-commit hooks; `.editorconfig`.
- Repository tests: Markdown links/images/anchors, `.env.example` vs settings actually read, version consistency, SHA-pinned actions,
  no committed secrets or data files. State-machine guard tests.
- Release workflow (tag-triggered, verifies the tag matches the app version and the CHANGELOG), label taxonomy and sync workflow,
  issue forms, pull request template, governance and developer documentation, real screenshots and a social preview image.

### Fixed
- The sidebar's last links were hidden behind the Local services panel on shorter windows (e.g. 1280×820); the menu now scrolls on
  its own and the panel folds when space is short.
- A running adaptive interview showed "Question 1 of 1" on the dashboard and the Active interview bar; it now shows the planned total.
- The documented and launcher-enforced Node.js minimum was 18, but the build tool needs 20.19+ or 22.12+ (and the frontend tests
  22.12+): users on Node 18–20.18 or 22.0–22.11 passed `check` and then failed to build. The launcher now checks major.minor, the
  docs say 20.19+/22.12+, `frontend/package.json` declares `engines`, and the Linux hint no longer suggests the (too old) apt package.
- Two `useMemo` hooks recomputed on every render; an unused value and a missing exception chain in the backend; a malformed
  `eslint-disable` comment.
- `.env.example` now documents `CLOUD_TIMEOUT_S`, `CLOUD_IDLE_TIMEOUT_S`, `CLOUD_MAX_TOKENS` and `ALLOW_NON_LOCAL_OLLAMA`.

### Security
- The API explorer pages (`/api/docs`, `/redoc`) loaded JavaScript and CSS from a public CDN, contrary to the "only localhost"
  promise. They are now off by default; developers can enable `/api/docs` with `API_DOCS=1`. `/api/openapi.json` is unchanged.
- `puppeteer-core` (development only, used by the e2e scripts) upgraded 24 → 25, removing two high-severity transitive advisories
  (`basic-ftp`, `extract-zip`) that were reachable only through code paths the scripts never use.
- Resume lines that look like instructions to an AI are flagged and excluded from offline questions and excerpts.
- Backups are written inside the private data folder (never the shared temp folder) and removed after download.

### Added
- **Interview Intelligence 2.0** ([docs/evaluation.md](docs/evaluation.md)): category evaluation profiles (SQL, Python, data
  engineering, ML, system design, software engineering, behavioural, general) with extra dimensions (conceptual understanding,
  problem-solving, edge cases, trade-offs); verbatim evidence quotes verified against the answer; ungrounded "misconceptions" shown but
  never counted; deterministic consistency rules; answer classification (correct / correct but incomplete / partially correct /
  incorrect / no attempt / uncertain); provenance on every evaluation (prompt, profile and rubric versions, model route, temperature,
  input hash). Still one grading call per answer.
- **Adaptive interviews** ([docs/adaptive-interviews.md](docs/adaptive-interviews.md)): a question pool and a deterministic engine with
  six strategies (progressive, deep-dive, practical, conceptual, mixed, resume-based), four levels with confidence-weighted, cool-down
  and anti-oscillation rules, topic coverage, one revisit of weak topics, evidence-based early end, and clarify / deepen / scenario /
  probe-gap follow-ups with a loop guard. Every decision is persisted with a plain-language reason.
- **Time limits** for fixed and adaptive interviews (paused time excluded).
- **Candidate profile** for every resume ([docs/resume-intelligence.md](docs/resume-intelligence.md)): skill inventory with
  evidence-based confidence and source line references, extraction-quality check against the raw text, projects, experience summary
  and gaps, technology relationships, clarification areas, prompt-injection warnings, practice history and unexplored areas. Offline,
  no model call.
- **Offline claim-grounded resume questions** (`resume_auto`): technology implications and a project deep-dive progression, each tied
  to its resume excerpt; same per-resume cloud-consent rule as AI-written questions.
- **Report analytics**: classification breakdown, difficulty-wise and conceptual-vs-practical performance, profile usage, progress per
  topic versus your previous attempt, learning plan, adaptive decision timeline, resume coverage.
- **Share-safe exports** (`?redact=true`, PDF/Markdown/JSON): allow-list of scores and topics; answers, grader prose, follow-ups,
  resume names, labels and excerpts removed.
- **Database backup download** (`GET /api/backup`, Settings → Profile) and a read-only evaluation-profile view in Settings.
- Docs: architecture decision records, contribution guide, security policy, issue/PR templates, tag-triggered release workflow.

### Changed
- Questions that match a category profile are scored with that profile's weights, so their scores can differ from 1.x. Uncategorised
  questions use the *general* profile, identical to 1.x. Your rubric weights in Settings still apply to every profile.
- A short answer containing "I don't know" that the grader still found nothing of value in is capped at 2 per dimension.
- Database schema v6 (additive: new columns and tables; existing data untouched; upgrades automatically from every earlier version).

## 1.0.0 (untagged)

The first public version of the repository (commits `2b07ee2` and `900f970`; the version number in the code was 1.0.0, but no
Git tag or GitHub release was created): local mock interviews with a question bank, spoken questions, Whisper microphone input,
follow-ups, reports, resumes and optional Ollama cloud mode.
