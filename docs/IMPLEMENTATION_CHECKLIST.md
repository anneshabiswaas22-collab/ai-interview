# Ordered Implementation Checklist (29 Gates)

> **All 29 product milestones are pending until accepted evidence exists.** Completed project documentation and an experimental framework-neutral core do not mean the end-user product is complete. Every gate requires actual execution, tests, privacy/security checks and updated documentation. Source of truth: [Implementation status](IMPLEMENTATION_STATUS.md).

## Phase 1: Architecture and foundation

- [ ] **01 — Euron runtime audit:** Pin source, run build/unit/integration/demo, review security/licenses, distinguish mock vs real voice. [Issue #1](https://github.com/anneshabiswaas22-collab/ai-interview/issues/1). Gate: real logs + adoption ADR.
- [ ] **02 — Alternative/component audit:** DeepInterview, GrillKit, LiveKit, Piston, Excalidraw, Promptfoo, Langfuse, Unsloth, vLLM. [Issue #2](https://github.com/anneshabiswaas22-collab/ai-interview/issues/2). Gate: pinned license/quality review.
- [ ] **03 — Choose foundation:** Adopt Euron if audited or document another choice. Gate: approved ADR, upstream attribution, integration map.
- [ ] **04 — Establish runnable monorepo:** Import/adapt accepted code, package locks, Docker/DB, migrations, CI and development setup. Gate: clean checkout builds and runs.
- [ ] **05 — Finalize API/state/schema:** Server-owned session, event, version, idempotency, permissions and rubric contracts. [Issue #3](https://github.com/anneshabiswaas22-collab/ai-interview/issues/3). Gate: executable contract tests.

## Phase 2: Candidate product MVP

- [ ] **06 — Authentication and dashboard:** Actual accounts, user-scoped profiles, interviews and admin permissions. Gate: cross-user access tests.
- [ ] **07 — Interview setup:** Role/seniority/time, upload-safe resume/JD parsing, consent and validation. Gate: end-to-end context tests.
- [ ] **08 — Adaptive interviewing:** Real model adapter, interview plan, follow-up reasoning, limits and robust transitions. Gate: real-provider, held-out conversational tests.
- [ ] **09 — Session persistence:** Durable transcript/events, reconnect, version conflicts and safe retry. Gate: survives restart.
- [ ] **10 — Reliable scoring:** Independent evidence-backed rubric evaluator, uncertainty and deterministic code results. Gate: expert-reviewed samples.
- [ ] **11 — Report and practice history:** Saved feedback, review, progress and export. Gate: [Issue #4](https://github.com/anneshabiswaas22-collab/ai-interview/issues/4) complete from authenticated setup to saved report.

## Phase 3: Advanced interviewer

- [ ] **12 — Realtime voice:** STT/LLM/TTS, interruptions, captions, consent, quotas and fallback. [Issue #6](https://github.com/anneshabiswaas22-collab/ai-interview/issues/6). Gate: real mic/reconnect tests.
- [ ] **13 — Coding assessments:** Editor, self-hosted isolated Piston or vetted alternative, public/hidden tests and security. [Issue #7](https://github.com/anneshabiswaas22-collab/ai-interview/issues/7). Gate: hostile-input security approval.
- [ ] **14 — Whiteboard:** Excalidraw with persisted diagrams, grounded explanation, accessibility. [Issue #8](https://github.com/anneshabiswaas22-collab/ai-interview/issues/8). Gate: save/reopen/replay.
- [ ] **15 — Interview replay and question content:** Versioned question packs, code/diagram/transcript synchronization, copyrighted-content checks. Gate: replay accuracy.
- [ ] **16 — Coaching analytics:** Competency-level improvement plans, stable rubrics and repeat-session comparisons. Gate: visible, evidence-based longitudinal usefulness.

## Phase 4: Own AI model and evaluation

- [ ] **17 — Baseline model evaluation:** Golden scenarios, Promptfoo, expert adjudication, prompt-injection tests. [Issue #5](https://github.com/anneshabiswaas22-collab/ai-interview/issues/5). Gate: measured baseline results.
- [ ] **18 — Legal training data:** Original/licensed multi-turn conversation dataset, provenance, consent, de-duplication and held-out splits. Gate: privacy/data audit.
- [ ] **19 — QLoRA pipeline:** Exact Qwen checkpoint license, Unsloth + PEFT/TRL scripts, external Colab/GPU notebooks and manifest. Gate: reproducible GPU training command.
- [ ] **20 — Run/compare fine-tune:** Actually train and benchmark adapters against base model, including latency/cost/regressions. [Issue #9](https://github.com/anneshabiswaas22-collab/ai-interview/issues/9). Gate: recorded held-out improvement or decline.
- [ ] **21 — Model serving:** vLLM or suitable inference provider, routing, rollback and spending caps. Gate: real serving tests, no untracked provider call.

## Phase 5: Production and business

- [ ] **22 — Pricing, quotas, payments:** Metered entitlements, selected payment provider, webhook retries and refunds. Gate: simulated billing consistency.
- [ ] **23 — Deploy and operate:** Hosting, HTTPS, monitoring, backups, incidents, disaster recovery, cost tracking. Gate: restoration and load verification.
- [ ] **24 — Security, privacy and accessibility:** Tenant auth, prompt-injection and code sandbox review, consent, deletion/export, accessibility. [Issue #10](https://github.com/anneshabiswaas22-collab/ai-interview/issues/10). Gate: independent review.
- [ ] **25 — Private beta and launch:** Moderated interviews, experience research, technical accuracy, retention, cost, documented limitations. Gate: user-tested release sign-off.

## Phase 6: Enterprise / market expansion

- [ ] **26 — Organizations and recruiter workflows:** Multi-tenancy, reviewers, invitation and audit controls. Gate: tenant-isolation test suite.
- [ ] **27 — Validated employer assessments:** Job-relevant rubrics, accessibility, human decision review, appropriate jurisdiction-specific compliance. Gate: independent validity/fairness review.
- [ ] **28 — ATS and enterprise APIs:** Documented integrations, webhooks, retries, access controls, SLAs. Gate: interoperability tests.
- [ ] **29 — Continuous competitive benchmarking:** Compare candidate experience, feedback, voice latency, coding accuracy and cost with market benchmarks using dated public evidence. Gate: measured iterative improvements.

## Verified groundwork (not equivalent to a finished milestone)

- [x] Initial requirements, architecture, license/reuse documents, developer instructions and 10 issues published.
- [x] Upstream repository sources inspected through GitHub API; initial source files and stub voice behavior found.
- [ ] Standalone interview-core tests to be verified in CI after initial branch push.
- [ ] Euron full runtime evaluation (blocked in this terminal: GitHub DNS and Docker; see [Codex handoff](CODEX_BLOCKERS.md)).

## Development gate rules

1. Never treat upstream README feature claims as implemented in our repository.
2. Keep one main application architecture; don't merge entire unrelated applications.
3. No fine-tuning without permissioned data and baseline evaluation.
4. No public code runner without isolated sandbox security review.
5. No real-voice claims based on browser speech stubs.
6. No automated hiring decisions from unvalidated model scores.
7. After each PR, link real test output and update this checklist + [status](IMPLEMENTATION_STATUS.md).
