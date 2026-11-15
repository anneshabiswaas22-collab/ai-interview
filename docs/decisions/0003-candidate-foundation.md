# ADR 0003 — Provisional candidate application foundation

- **Status:** Development preview; production adoption remains gated
- **Date:** 2026-11-14

## Decision

Import one pinned, MIT-licensed Euron application into `foundation/euron` as the working candidate foundation. Retain its license, relevant runtime components and lockfile; do not import DeepInterview as a second app. Keep `packages/interview-core` as an experimental policy module until a single authoritative interview state model is selected.

The pinned upstream built and passed 232 unit and 150 PostgreSQL/Redis integration tests. Its unmodified browser suite failed one signup test because the test assumed immediate sign-in when email verification was required; a verification-aware version passed all eight tests. A Zod 4.6.7 update removed the reported production dependency advisory in the test environment. A separate integration failure exposed an export audit race, fixed by recording export access before streaming. See [the verification run](https://github.com/anneshabiswaas22-collab/ai-interview/actions/runs/43519071316).

## Scope and acceptance

This decision permits local development and test demonstrations only. It does not declare production security, fairness, compliance, model quality or commercial licensing complete. The imported app remains responsible for its own authentication and database; do not add a competing authentication or session system. Retain upstream notices and track all adaptations.

Before the first real candidate-facing release:

1. Replace client-authored interviewer transcript and position controls with a server-authoritative, transactional event stream and safe retries.
2. Connect a separately validated, evidence-backed evaluator; do not mistake exact quotation checks or stub scores for correct assessment.
3. Complete consent, provider data-handling, deletion, accessibility and security reviews; keep audio recording and camera proctoring off by default.
4. Complete the transitive license/SBOM and model asset review. Verify each real provider, costs and usage limits with permissioned test data.
5. Pass clean-checkout unit, integration, browser and adversarial tests for the actual imported application.

## Rollback

The foundation is isolated under one directory. Reverting the import and its dedicated workflow restores the earlier standalone policy prototype and documents without changing candidate data; no production data migration is introduced here.
