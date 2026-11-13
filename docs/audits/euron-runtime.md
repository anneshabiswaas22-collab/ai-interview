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
5. **Supply chain:** `corepack pnpm audit --prod` on 2026-11-14 reported one high advisory, [GHSA-mrhx-c7xc-m3w5](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5), with a finding for Zod 3.25.76. The pinned lockfile lists that version directly for the API and web app. The tool reported affected versions below 4.6.6 and did not supply dependency paths in its finding. Assess reachability and migrate to a patched compatible version with tests; this is a major-version change, not a blind lockfile bump. A pinned checkout and MIT top-level license do not establish dependency, asset or vulnerability clearance. Complete the SBOM and asset/model license review before import or deployment.
6. **Signup browser check:** the unmodified offline browser suite failed its signup test twice because its expected signed-in home heading did not appear after submitting the form. Seven other browser tests passed. The test assumes immediate login, whereas the app handles a `202` response by asking for email verification. In a separate diagnostic, following the existing verification link allowed all eight browser tests to pass. The unmodified baseline remains failed; do not relabel it as passing.

## Runtime evidence

| Check | Result |
| --- | --- |
| `git clone` and checkout of the two pinned commits | Passed in a disposable workspace. |
| `node --test packages/interview-core/test/*.test.mjs` | 11 passed in our repository. |
| `python3 scripts/check_docs.py` | Passed before this audit change. |
| Euron dependency-free stub HTTP smoke | Passed: HTTP 200 and a four-round deterministic plan for Backend Engineer; no real model call. |
| Euron install, lint, typecheck, build, OpenAPI, sanitization and unit tests | Passed on GitHub Actions at the pinned upstream source: 232 unit tests passed. See [audit run](https://github.com/anneshabiswaas22-collab/ai-interview/actions/runs/43516008206). |
| Postgres/Redis integration | Passed on GitHub Actions: 150 tests against isolated Postgres 16 and Redis 7, using provider stubs. Docker and local Postgres/Redis were unavailable locally. |
| Complete offline browser demo | Stack startup and demo seed passed. Unmodified `pnpm e2e`: 7 passed, 1 failed (signup, including retry). See the audit run; not a fully passing end-to-end demo. |
| `corepack pnpm audit --prod` | Failed with one high Zod advisory; 471 production dependencies scanned. No dependency paths were returned by the audit tool. |
| Verification-aware signup diagnostic | Passed all 8 offline browser tests after changing only the signup test in a disposable checkout to follow the verification link. See [diagnostic run](https://github.com/anneshabiswaas22-collab/ai-interview/actions/runs/43517392742). The workflow still reports failure because it preserves the original failed baseline and dependency finding. |
| Zod remediation candidate | A [separate patch](https://github.com/anneshabiswaas22-collab/ai-interview/pull/15) upgraded Zod and changed export auditing to occur before streaming. Its [revised verification run](https://github.com/anneshabiswaas22-collab/ai-interview/actions/runs/43519071316) passed the production advisory scan, build, 232 unit tests, 150 database integration tests and 8 offline browser tests using the verification-aware signup adjustment. The first patched run had exposed the export-audit race with a 149/150 integration result. The patch still needs review before adoption. |
| Real model/voice/microphone | Not run; no provider or microphone test is implied by the stub. |
| Security, accessibility, data handling and dependency audit | Partial source inspection only; not approved. |

## Recommendation and gate

Euron remains the leading reuse candidate, but **do not import it or declare the architecture adopted** until the browser failure and high dependency advisory are resolved, and the above evidence, event, privacy and dependency gaps have a concrete integration plan. Avoid building another complete auth, database, or interview application alongside it. The existing interview core is a prototype, not yet the production source of truth. Use one eventual session contract and one auth/database stack.

The next code can be a portable feedback/evidence contract that is independent of the foundation and can be integrated into whichever single application is selected. It must not claim that exact quotations establish the truth or fairness of a score.
