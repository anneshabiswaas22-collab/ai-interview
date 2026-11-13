# Euron foundation audit

Reviewed: 2026-11-14. This is an in-progress audit, not adoption or a security certification.

## Exact sources

- Euron: [216a8fc52a055587f436f2446f1a80b6868bd14a](https://github.com/euron-sde-team/euron-open-real-time-ai-conversation-system/tree/216a8fc52a055587f436f2446f1a80b6868bd14a).
- DeepInterview comparison: [bd6d136fffc509265bc2355e95101e0ad7f56eac](https://github.com/ngoanpv/DeepInterview/tree/bd6d136fffc509265bc2355e95101e0ad7f56eac).
- Euron's LICENSE at that revision is MIT, copyright ENGAGESPHERE TECHNOLOGY PRIVATE LIMITED and contributors. Retain the copyright and full permission notice for any substantial source copied. No Euron code or assets were imported by this audit. Dependency, asset and model licenses still require review.
- DeepInterview's LICENSE is Apache-2.0 and it has a NOTICE file. Its separate Python agent, Next.js application and LiveKit/Supabase architecture overlap with Euron; do not import a second application merely to get similar capabilities.

## What source inspection established

Euron contains a Next.js web application, Express API, Postgres migrations, Redis-backed jobs, server-side authentication and quota services, model adapters, report and sharing endpoints, an editor, and a separate deterministic provider stub. Its API includes owner-scoped interview lookup and an answer endpoint that rejects client-supplied ratings. The source also contains integration and browser test suites. These are source findings, not a claim that those features work in this repository or are production-secure.

The [upstream checks run at the pinned commit](https://github.com/euron-sde-team/euron-open-real-time-ai-conversation-system/actions/runs/40654759929) reports success. It is useful upstream evidence for its checks, but is not evidence that its optional full-stack, integration, or real-provider suites ran in our environment.

## Material gaps to resolve before adoption

1. **Evidence and grading:** the scoring output in `apps/api/src/services/interview/prompts.ts` asks for numerical ratings and narrative without transcript evidence IDs or exact quotations. The schema in `apps/api/src/jobs/interview.jobs.ts` validates rating ranges, not whether claims are supported. Code correctness is model-judged, not verified through an isolated test runner. Align with our evidence contract and label uncertain results; validate quality with experts before relying on scores.
2. **Server-owned event history and retries:** `apps/api/src/services/interview/interview.service.ts` receives transcript lines and question coordinates from the browser, accepts `interviewer` as well as `candidate` lines, and replaces an existing answer for the question. Its progression uses the supplied coordinates. This is different from our append-only, server-authoritative event and idempotency requirements. Determine how to establish trustworthy interviewer events, constrain positions and handle retries before treating reports as authoritative. A candidate editing their own practice data is different from a cross-account access finding; no such cross-account exploit is asserted here.
3. **Demo vs actual AI:** `apps/stubs/server.mjs` uses a deterministic plan and length-based scoring. Its code stub considers simple text patterns, not code execution. The stub is useful for plumbing tests only and must never be presented as a real assessment or provider test.
4. **Consent and features:** proctoring is off by default in the database and normal creation paths, but the demo seed enables it for its sample user. Our practice experience must preserve explicit consent and remain usable without camera/proctoring. Review analytics, audio, model-provider data handling and training consent before any public use.
5. **Supply chain:** the Euron lockfile contains hundreds of packages. A pinned source checkout and MIT top-level license do not establish transitive dependency, asset or vulnerability clearance. Complete a dependency/SBOM and asset license review, including model files, before import or deployment.

## Runtime evidence

| Check | Result |
| --- | --- |
| `git clone` and checkout of the two pinned commits | Passed in a disposable workspace. |
| `node --test packages/interview-core/test/*.test.mjs` | 11 passed in our repository. |
| `python3 scripts/check_docs.py` | Passed before this audit change. |
| Euron dependency-free stub HTTP smoke | Passed: HTTP 200 and a four-round deterministic plan for Backend Engineer; no real model call. |
| Euron install, build, unit tests | In progress; record the commands and actual results before closing the gate. |
| Postgres/Redis integration and complete browser demo | Not yet locally verified: Docker and local Postgres/Redis executables were absent in this environment. The repository workflow `.github/workflows/euron-audit.yml` supplies isolated GitHub-hosted test services and the upstream offline demo; its result must be checked, not presumed. |
| Real model/voice/microphone | Not run; no provider or microphone test is implied by the stub. |
| Security, accessibility, data handling and dependency audit | Partial source inspection only; not approved. |

## Recommendation and gate

Euron remains the leading reuse candidate, but **do not import it or declare the architecture adopted** until the pinned source's build, integration and browser checks are observed and the above evidence, event, privacy and dependency gaps have a concrete integration plan. Avoid building another complete auth, database, or interview application alongside it. The existing interview core is a prototype, not yet the production source of truth. Use one eventual session contract and one auth/database stack.

The next code can be a portable feedback/evidence contract that is independent of the foundation and can be integrated into whichever single application is selected. It must not claim that exact quotations establish the truth or fairness of a score.
