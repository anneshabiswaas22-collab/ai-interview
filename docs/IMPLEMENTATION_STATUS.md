# Implementation Status — 2026-11-15

## Development candidate

An adapted Euron application is included in [foundation/euron](../foundation/euron/README.md). It contains the candidate UI, API, database migrations, job worker, provider adapters and local demo infrastructure. It is a development preview and has not been approved for production or deployed. See [ADR 0003](decisions/0003-candidate-foundation.md) and [third-party notices](../THIRD_PARTY_NOTICES.md).

The pinned patched upstream candidate previously passed [232 unit tests, 150 PostgreSQL/Redis integration tests and 8 browser tests](https://github.com/anneshabiswaas22-collab/ai-interview/actions/runs/43519071316). The browser tests used a verification-aware signup test. The imported copy also passed its own [clean-checkout unit, PostgreSQL/Redis integration and offline browser workflow](https://github.com/anneshabiswaas22-collab/ai-interview/actions/runs/43583803264).

## Text practice slice

A consent-based written practice mode is implemented on the existing application database and authentication. The server chooses questions from the frozen plan, stores the conversation, and serializes retries and concurrent answers. It exports and deletes its own records with the interview. The separate voice mode still uses browser-authored transcript data. Its [clean-checkout PostgreSQL/Redis integration and offline browser workflow](https://github.com/anneshabiswaas22-collab/ai-interview/actions/runs/43584618534) passed with simulated providers.

Written practice now has an evidence-backed evaluation candidate: it uses an explicit four-criterion rubric, requires exact quotations from the server-owned text-practice ANSWER event, validates those quotations before including a criterion in aggregate scores, records provider/model/rubric provenance in feedback JSON, and displays supported, uncertain and unsupported findings in the report. Low-confidence and invalid-evidence criteria are excluded from aggregate ratings, and a missing response is not converted into an automatic failing score. This establishes provenance only; it does **not** establish that a model's technical judgment is correct or fair. Real-provider behavior and expert-reviewed scoring quality remain unvalidated. The default local provider is simulated.

Voice and code answers still use the legacy evaluator. Voice transcripts are still browser-authored, and code correctness is still model-judged rather than executed in an isolated runner. The transactional score-dispatch outbox is retained; planning and other jobs still use best-effort dispatch. The evidence-backed change must pass its pull-request clean-checkout unit, PostgreSQL/Redis integration, build and browser workflows before it is treated as verified.

## Experimental policy core

`packages/interview-core` is a standalone session-policy prototype with its own Node tests. It is not connected to the imported application's authentication, database or model adapters. Do not present it as a second production session engine.

## Highest priorities

1. Verify the evidence-backed written-feedback change with clean-checkout unit, database and browser checks.
2. Build an expert-reviewed golden set and measure technical correctness, calibration and coaching usefulness with at least one authorized real provider.
3. Make adaptive session position, interviewer events, retries and voice transcripts server-authoritative with transactional persistence.
4. Complete privacy, accessibility, security and dependency-license reviews before a public release.

The default local demo uses simulated model responses and scores. Real voice, real model quality, fine-tuning and production deployment have not been verified.
