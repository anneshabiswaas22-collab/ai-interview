# Codex Handoff — Current Status and Blockers

The pinned candidate application is imported under `foundation/euron`. Its clean-checkout unit, PostgreSQL/Redis integration and offline browser tests passed with simulated providers. Written practice, persisted questions and answers, retries, and a scoring-dispatch recovery path are implemented in the development branches. Read [implementation status](IMPLEMENTATION_STATUS.md), [the implementation checklist](IMPLEMENTATION_CHECKLIST.md), [text-practice contract](TEXT_PRACTICE_DEVELOPMENT.md), [foundation decision](decisions/0003-candidate-foundation.md), and [runtime audit](audits/euron-runtime.md).

## Work still required

1. Integrate evidence-backed feedback using the existing application's authentication and database. Evaluate technical accuracy and usefulness against an expert-reviewed dataset; provenance checks alone do not prove correctness or fairness.
2. Validate real model providers, voice, transcription, interruptions, reconnection, consent, latency and costs. The local stub's answers and scores are demonstrations, not evaluations of a candidate.
3. Implement isolated, quota-limited untrusted-code execution before executing candidate code. The current editor is not a secure execution service.
4. Complete application security, accessibility, privacy, data-retention, dependency-license and independent release review before public use. The text mode does not use a camera; the separate voice path still has browser-authored transcripts.
5. Implement and test the remaining roadmap, including whiteboard, progress, billing, operations and other features as prioritized in the checklist. Production hosting, provider keys, monitoring, backups and a budget must be supplied and verified separately.
6. Any model training requires licensed, consented data, a checkpoint-specific license review, an authorized GPU and a reproducible held-out evaluation. Do not assume a fine-tune improves results.

The local terminal used for this work lacked Docker, so clean runtime and browser checks were executed in GitHub Actions. This is an environment limitation, not a claim that Docker is universally unavailable. An earlier GitHub DNS failure was resolved by the time the pinned source was imported; do not repeat that checkout audit without a reason. Never place secrets, real resumes or candidate recordings in the repository.

## Copy-ready instruction

Read `AGENTS.md`, `docs/IMPLEMENTATION_CHECKLIST.md` and `docs/IMPLEMENTATION_STATUS.md`. Use the imported application and existing auth/database. Pick the next scoped issue, implement and test it, record the actual evidence and limitations, and submit a small reviewable PR. Do not claim the stub is a real AI evaluation or that the product is ready for public use.
