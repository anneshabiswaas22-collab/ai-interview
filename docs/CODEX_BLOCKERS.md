# Codex Handoff — Immediate Blockers

> Update 2026-11-14: The pinned candidate application is now available in `foundation/euron` for development. See [implementation status](IMPLEMENTATION_STATUS.md), [the foundation decision](decisions/0003-candidate-foundation.md) and [the runtime audit](audits/euron-runtime.md). The earlier checkout blocker below is historical; production security, authoritative transcripts and real-provider validation remain open.

## B1: Euron checkout and runtime tests

**Observed:** GitHub connector can read source and write to this repository. Terminal command `git ls-remote https://github.com/euron-sde-team/euron-open-real-time-ai-conversation-system.git HEAD` failed with `Could not resolve host: github.com`. The execution sandbox has Node 22 and TypeScript but no Docker executable.

**Exact Codex task:**
1. Connect Codex Cloud to this repository and read `AGENTS.md`, `docs/IMPLEMENTATION_CHECKLIST.md`, `docs/UPSTREAM_SOURCES.md` and [issue #1](https://github.com/anneshabiswaas22-collab/ai-interview/issues/1).
2. Clone Euron at pinned SHA `216a8fc52a055587f436f2446f1a80b6868bd14a` into a temporary worktree (not over this project).
3. Review its MIT LICENSE, packages, dependency security and actual auth, plan, voice, scoring, editor, admin and quota implementations.
4. Run documented build, unit, integration, offline demo and relevant browser tests wherever resources support them; record exact commands and pass/fail/skip.
5. Separate offline stub voice from hosted OpenAI/Gemini real-time speech. Do not claim a test run if skipped for lack of Docker/network/API key.
6. Write `docs/audits/euron.md` and a justified ADR choosing adoption/partial reuse/alternate. Preserve upstream notices and existing project documentation.
7. Review our `packages/interview-core` prototype; do not create competing state machines without need. Open scoped PR for review.

**If network still fails:** Report exact credentials/DNS/proxy errors. Obtain approved access or a vetted source archive; never invent results.

## B2: External production resources (not needed for core tests)

- Real voice needs provider/LiveKit configuration and mic test.
- Model training needs an authorized GPU, checkpoint-specific license and reviewed datasets.
- Production needs hosting, secrets, database, backups, HTTPS and cost budget.
- Payments need an eligible regional provider account.

Never share secrets in issues, code or chat. Keep features scoped; start with the runtime foundation audit before any large import.

## Copy-ready short Codex instruction

Read AGENTS.md and docs/IMPLEMENTATION_CHECKLIST.md. Complete issue #1 first: clone/test the pinned Euron source, verify real vs mock features, source licenses and safety, and submit an evidence-based adoption ADR. Run the existing framework-neutral core tests on branch feat/bootstrap-interview-core and avoid duplicate development. Report exact blockers and open a small PR; do not blindly merge all upstream apps.
