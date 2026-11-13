# Developer Onboarding and Local Setup

**CURRENT STATE:** This repository includes documentation plus a dependency-free interview-core module. No candidate-facing application, model checkpoint, database migrations or production deployment exists. The core unit suite has passed on GitHub Actions. Commands for Euron below are upstream audit instructions, not proof they work here.

## Step 1 — Obtain the source

```bash
git clone https://github.com/anneshabiswaas22-collab/ai-interview.git
cd ai-interview
git status
```

Read `README.md`, `AGENTS.md`, `docs/VISION.md`, `docs/ROADMAP.md`, `docs/REUSE_VS_BUILD.md`, `docs/LICENSE_AUDIT.md`.

## Run the first executable unit suite

Requires Node.js 22 or newer, no install or API keys:

```bash
node --test packages/interview-core/test/*.test.mjs
```

This verifies session policy only, not an application or AI provider.

## Step 2 — Review the first milestone

Start by auditing the candidate foundation rather than writing a new UI:
- [Euron main application](https://github.com/euron-sde-team/euron-open-real-time-ai-conversation-system)
- [DeepInterview agent patterns](https://github.com/ngoanpv/DeepInterview)
- [GrillKit technical training](https://github.com/Forkfield/grillkit)

Pin their commit SHAs, read README/license, inspect whether the claimed feature uses a real provider or a mock, and run their documented build/test commands in disposable folders. Use no real candidate data or secrets.

## Step 3 — Upstream audit sample (not our app setup)

```bash
git clone https://github.com/euron-sde-team/euron-open-real-time-ai-conversation-system.git
cd euron-open-real-time-ai-conversation-system
git rev-parse HEAD
git status
# Read upstream README and Makefile before executing install/demo commands.
# Run its documented tests in an isolated container or local environment.
```

Do not copy the Euron repository into this GitHub repo until the PR documents licensing, actual runtime results, dependencies, security risks and a proposed migration plan.

## Step 4 — Future local environment, after foundation accepted

Expected tools (confirm versions with chosen upstream): Node.js/pnpm, Python for ML/voice services, Docker Compose, PostgreSQL, Redis and suitable editor. Training GPU is **not** required for everyday app development. Establish `.env.example` with fake/sample placeholders only.

Once runnable code is imported, this guide must be updated with:
1. Pinned versions and prerequisites.
2. Exact install/migration/test commands.
3. How to launch web, API, worker and safe mock providers.
4. How to configure real providers without storing secrets.
5. Test fixtures and reset/seed instructions.
6. Troubleshooting and observability.
7. Exact launch and production deploy limitations.

Until those are present, **do not claim `npm run dev`, `pnpm dev` or `docker compose up` works in this repository.**

## Contributing safely

Use a feature branch and create a scoped PR with the [template](../.github/PULL_REQUEST_TEMPLATE.md). For architecture-changing imports, write an ADR. Follow the security/privacy guide and do not upload user resumes or confidential interview recordings. Review is required before high-risk code merges.

## Suggested first contributor deliverable

An audit PR with a pinned Euron SHA; documented test and demo results; inventory of real vs stubbed capabilities; license/SBOM notes; comparison with DeepInterview; a suggested stack and the first code PR acceptance tests.

This is enough for contributors to proceed without access to any prior chat.
