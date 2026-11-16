# AI Interview Platform — Master Project Handoff and Durable Memory

Last consolidated: 2026-11-16  
Repository: https://github.com/anneshabiswaas22-collab/ai-interview  
Main branch snapshot used for this handoff: 08af53c16753bd8a3e580de32760a9c02e5def60  
Current evidence-feedback PR at consolidation time: https://github.com/anneshabiswaas22-collab/ai-interview/pull/22  
PR #22 head at consolidation time: 13b9db99b4f6d4c911e6c43337d4fc656db4f595

## Why this document exists

This file is the durable project memory for the AI Interview Platform.

The owner explicitly requested that future ChatGPT, Codex, developers and reviewers should not depend on a long chat transcript to understand the project. Long chats can be hard to reload, easy to lose and may contain old statements that no longer match the code.

Use this document together with the repository source and the documents linked below. Actual source code and recent verified tests always override stale planning text.

This is a curated, comprehensive record of the substantive discussion, research, architecture decisions, repository findings, implementation work, test evidence, risks and next steps. It intentionally avoids copying redundant conversational filler or low-level tool chatter.

## 1. Mission

Build an independently branded, self-hostable, commercially competitive AI interview-preparation platform.

Primary initial audience:

- software-engineering candidates;
- candidates preparing behavioral and technical interviews;
- users needing realistic text and voice practice;
- candidates who want technically relevant, evidence-backed coaching rather than generic encouragement.

Longer-term capabilities:

- adaptive conversational follow-ups;
- resume-aware and job-description-aware interview plans;
- voice interviews;
- coding exercises with deterministic execution;
- system-design whiteboards;
- evidence-backed evaluation;
- personalized improvement plans;
- session history and progress;
- provider-neutral LLM integration;
- optional self-hosted/fine-tuned models;
- privacy, security, budget and cost controls;
- possible employer workflows only in later phases after candidate-practice quality is established.

The product must not become a collection of loosely merged public repositories. The desired end state is one owned product, one authoritative interview session model and one coherent architecture.

## 2. Engineering principles agreed during the project

1. Build on what already works.
2. Research before rewriting.
3. The current Euron-derived application is the development foundation unless a serious, evidence-backed reason justifies replacing it.
4. DeepInterview is an interview-intelligence reference, not a second application.
5. One codebase. One authoritative session model.
6. Do not present mocks or deterministic stubs as real AI quality.
7. Do not present browser-only code editing as secure code execution.
8. Do not present browser-owned voice transcripts as authoritative evidence.
9. Do not treat evidence provenance as proof that an AI score is technically correct.
10. Do not fine-tune before establishing a measured baseline and an expert-reviewed evaluation set.
11. Do not add premature microservices.
12. Keep external providers replaceable.
13. All resumes, JDs, candidate answers and model outputs are untrusted.
14. No paid provider calls, public deployment, destructive repository changes or secret exposure without explicit approval.
15. Candidate practice feedback is not a validated hiring decision.
16. Future employer assessment requires separate validity, fairness, accessibility, legal and human-review work.

## 3. Source-of-truth precedence

When documents disagree, use this order:

1. Actual current source code.
2. Recent executed test/CI evidence.
3. Current ADRs and implementation-status documents.
4. This handoff.
5. Older planning documents and kickoff notes.
6. Upstream README claims.

Do not restart the original foundation-selection task merely because an old document still says Euron has not been imported.

## 4. Current repository truth

At the time of this handoff:

- main branch commit: 08af53c16753bd8a3e580de32760a9c02e5def60
- main already contains the adapted Euron application under foundation/euron
- packages/interview-core exists as an experimental policy/evidence prototype
- PR #22 contains the first production-path evidence-backed written-feedback implementation
- PR #22 is separate from main and must not be treated as merged until GitHub shows it merged

Key root structure:

~~~text
ai-interview/
├── foundation/euron/
│   ├── apps/
│   │   ├── web/
│   │   ├── api/
│   │   └── stubs/
│   ├── packages/
│   │   ├── types/
│   │   ├── api-client/
│   │   └── ui/
│   ├── db/migrations/
│   ├── deploy/
│   ├── infra/
│   └── e2e/
├── packages/interview-core/
├── docs/
├── AGENTS.md
├── CONTRIBUTING.md
└── REFERENCE_REPOSITORIES.txt
~~~

## 5. Exactly two main repositories selected

### 5.1 Euron Open Conversation — primary application foundation

URL:
https://github.com/euron-sde-team/euron-open-real-time-ai-conversation-system

Verified upstream revision studied:
216a8fc52a055587f436f2446f1a80b6868bd14a

License:
MIT

Role:
Primary application foundation.

Why it remains the correct foundation:

- the repository already contains an adapted copy;
- Next.js frontend fits the product;
- Express/TypeScript backend fits the existing codebase;
- PostgreSQL is already the source of truth;
- Redis/BullMQ is already used for background work;
- authentication, accounts, reports, history and admin structures already exist;
- model-provider abstractions already exist;
- realtime provider adapters already exist;
- there are existing deterministic stubs and broad test infrastructure;
- replacing it now would destroy working code and create unnecessary migration risk.

Important limitation:
The upstream repository has very shallow visible history at the pinned revision. Treat our fork as code we own and maintain, not as a dependency whose maintenance can be outsourced to upstream.

### 5.2 DeepInterview — interview-intelligence reference

URL:
https://github.com/ngoanpv/DeepInterview

Verified upstream revision studied:
bd6d136fffc509265bc2355e95101e0ad7f56eac

License:
Apache-2.0

Important upstream source areas studied:

- apps/agent/src/deepinterview_agent/prep/
- apps/agent/src/deepinterview_agent/live/
- apps/agent/src/deepinterview_agent/post/
- apps/agent/tests/test_adaptive.py
- apps/agent/tests/test_score.py

Role:
Secondary application-level architectural and interview-intelligence reference.

Useful concepts:

- separate preparation, live direction and post-evaluation responsibilities;
- answer-aware interview adaptation;
- competency/coverage tracking;
- deterministic difficulty/coverage policy tests;
- evaluator/verifier separation;
- skipping unanswered items rather than automatically grading them as incorrect;
- per-question evaluation boundaries;
- interview lifecycle limits and coaching structure.

Do not:

- import DeepInterview as a second application;
- add a parallel Python session backend;
- duplicate authentication, database ownership or job infrastructure.

Preferred approach:
Reimplement selected techniques in the existing TypeScript backend behind the existing API/database/session boundaries.

## 6. Architecture discovered in the live repository

### 6.1 High-level runtime

~~~mermaid
flowchart LR
    Candidate[Candidate Browser]
    Web[Next.js Web App]
    API[Express API]
    PG[(PostgreSQL)]
    Redis[(Redis / BullMQ)]
    Worker[Background Jobs]
    LLM[LLM Provider Adapters]
    Realtime[Realtime Voice Providers]
    Stub[Deterministic Stub Providers]
    Reports[Reports / PDF / History]

    Candidate --> Web
    Web --> API
    API --> PG
    API --> Redis
    Redis --> Worker
    Worker --> LLM
    Worker --> Stub
    API --> Realtime
    Worker --> PG
    PG --> Reports
    API --> Reports
~~~

### 6.2 Frontend responsibilities

Primary path:
foundation/euron/apps/web/src/

Implemented frontend areas include:

- authentication pages/state;
- candidate dashboard;
- interview creation/setup;
- interview plan/review;
- written text-practice flow;
- live interview room;
- CodeMirror-based code editor;
- interview history;
- report view;
- share/PDF-related workflows;
- settings/admin interfaces;
- API client integration;
- query/state helpers.

Important files include:

- foundation/euron/apps/web/src/components/interview/new-interview.tsx
- foundation/euron/apps/web/src/components/interview/interview-view.tsx
- foundation/euron/apps/web/src/components/interview/text-practice-view.tsx
- foundation/euron/apps/web/src/components/room/room-view.tsx
- foundation/euron/apps/web/src/components/room/code-editor.tsx
- foundation/euron/apps/web/src/components/report/report-body.tsx
- foundation/euron/apps/web/src/components/report/report-view.tsx
- foundation/euron/apps/web/src/lib/api.ts

Important distinction:
The code editor is an editor. It is not yet a secure isolated code runner.

### 6.3 Backend responsibilities

Primary path:
foundation/euron/apps/api/src/

Relevant areas:

- routes/
- controllers/
- services/interview/
- integrations/llm/
- integrations/realtime/
- jobs/
- repositories/
- middleware/
- security/
- db/

The current backend already supplies:

- authentication and user ownership checks;
- interview creation;
- resume/JD handling;
- interview planning;
- model selection;
- structured model calls;
- text-practice session persistence;
- score dispatch/retry;
- report generation;
- quota/usage tracking;
- provider/realtime configuration;
- admin functionality.

### 6.4 Database

Primary migrations:
foundation/euron/db/migrations/

Important tables/areas include:

- users and account/authentication state;
- interviews;
- answers;
- live sessions;
- proctoring events;
- share records;
- usage/audit records;
- text-practice sessions;
- text-practice events;
- text-practice requests;
- score dispatch/outbox records.

The written text-practice design is materially stronger than the legacy voice path because it has server-owned events, sequencing, versioning and request replay protection.

## 7. End-to-end written-practice data flow

~~~mermaid
sequenceDiagram
    participant U as Candidate
    participant W as Next.js Web
    participant A as Express API
    participant D as PostgreSQL
    participant Q as Redis/BullMQ
    participant J as Worker
    participant M as Model Adapter

    U->>W: Sign in / create interview
    W->>A: Resume or job description
    A->>D: Create interview
    A->>Q: Plan interview job
    Q->>J: Execute planning
    J->>M: Structured planning request
    M-->>J: Plan JSON
    J->>D: Persist interview plan

    U->>W: Start text practice with consent
    W->>A: Start text session
    A->>D: Create authoritative session/events

    U->>W: Submit written answer
    W->>A: Answer + requestId + expectedVersion
    A->>D: Transactionally persist ANSWER event
    A->>D: Record score dispatch
    A->>D: Advance authoritative position
    A->>Q: Dispatch scoring work

    Q->>J: Score answer
    J->>D: Load server-owned answer
    J->>M: Structured rubric evaluation
    M-->>J: Proposed assessment
    J->>J: Validate schema/evidence/uncertainty
    J->>D: Store validated feedback/provenance

    U->>W: View report
    W->>A: GET report
    A->>D: Load answers/scores/evidence
    A-->>W: Report/history
~~~

## 8. Implementation matrix

| Capability | Classification | Notes |
|---|---|---|
| Authentication/session ownership | Implemented and independently tested | Real API/database path |
| Dashboard/history | Implemented and independently tested | Covered in current application/test stack |
| Resume/JD interview creation | Implemented and independently tested with stubs | Real provider quality still requires authorized live-provider evaluation |
| Interview planning | Implemented with structured model output | Model-quality validation incomplete |
| Provider-neutral text adapters | Implemented but not live-verified in this research task | OpenAI, compatible, Anthropic, Gemini, stub |
| Server-authoritative text practice | Implemented and independently tested | Events, versioning, replay/idempotency |
| Durable score dispatch | Implemented and independently tested | Score outbox/recovery exists |
| Written evidence-backed scoring | Implemented on PR #22 and CI-tested | Not merged at consolidation time |
| Reports/history/PDF/share | Implemented and independently tested | Feedback quality depends on evaluator |
| Voice interview | Partially implemented | Browser-owned transcript authority remains a major weakness |
| Adaptive text follow-up | Partially implemented / planned | Current written practice follows a fixed stored plan |
| Coding editor | Implemented | CodeMirror editor |
| Secure code execution | Planned only | Must use isolated runner such as vetted Piston deployment |
| System-design whiteboard | Planned only | Excalidraw preferred candidate |
| Evidence-policy prototype | Experimental | packages/interview-core |
| Expert grading benchmark | Planned / next | Required before claiming AI scoring quality |
| Fine-tuning | Planned only | Do not start before baseline benchmark |
| Employer workflows | Planned later | Requires tenancy, audit, validity/fairness review |

## 9. Highest-value confirmed findings from the audit

### 9.1 Empty answers were being automatically failed

Confirmed behavior on main before PR #22:
foundation/euron/apps/api/src/jobs/interview.jobs.ts forced domain and communication scores to 1 when the candidate had not responded.

Why this matters:
Absence of evidence is not evidence of poor competency. It also biases averages.

PR #22 changes empty/no-response scoring to unscored/null.

### 9.2 Generic scoring lacked evidence provenance

The legacy score contract produced numeric ratings and prose feedback but did not require a claim to be tied to an authoritative stored candidate answer.

PR #22 introduces written-practice evidence validation.

### 9.3 Voice transcript authority is not sufficient for high-trust scoring

The current live-room frontend sends its transcript state back to the API when finalizing answers.

That means the browser is part of the evidence-authority path.

Required future change:
Persist transcript events from the trusted realtime/server path and use them as the assessment source.

### 9.4 Code editing is not code execution

The frontend contains CodeMirror. There is no production-grade sandboxed test execution path.

Do not describe the current coding workflow as deterministic technical assessment.

### 9.5 Exact quotations do not prove score correctness

A quote can be authentic while an evaluator's interpretation is wrong.

Therefore evaluation quality needs a separate expert-reviewed benchmark.

### 9.6 Written practice is not genuinely answer-adaptive yet

The current text-practice service advances through the stored plan.

Future work should make the follow-up policy answer-aware while keeping the server authoritative.

### 9.7 Scoring dispatch durability is stronger than planning dispatch

Score-outbox recovery is a good pattern.

Other important background operations, especially planning, may still use less durable best-effort dispatch.

Reuse the outbox pattern where justified rather than introducing another queue framework.

### 9.8 Experimental and production session logic can diverge

packages/interview-core contains useful tested state/evidence ideas but must not become a parallel production engine.

Port invariants into the real TypeScript application, test parity, then archive/reduce the prototype when appropriate.

### 9.9 Original-project license selection remains a release concern

The repository's own project licensing/ownership policy must be explicit before broad commercial distribution/contribution.

Upstream attribution does not replace a license decision for original project code.

### 9.10 Real-provider quality remains unverified

The deterministic stubs prove system behavior and contracts, not model correctness.

Do not advertise production AI quality based only on stub CI.

## 10. Evidence-backed feedback implementation — PR #22

PR:
https://github.com/anneshabiswaas22-collab/ai-interview/pull/22

Branch:
feat/evidence-backed-text-feedback

Head at consolidation:
13b9db99b4f6d4c911e6c43337d4fc656db4f595

Base:
08af53c16753bd8a3e580de32760a9c02e5def60

Purpose:
Make written-practice feedback traceable to actual candidate responses while keeping the existing application architecture.

Files changed at consolidation:

~~~text
docs/ARCHITECTURE.md
docs/IMPLEMENTATION_STATUS.md
docs/PROJECT_CONTEXT.md
docs/QUALITY_AND_TESTING.md
foundation/euron/apps/api/src/jobs/interview.jobs.ts
foundation/euron/apps/api/src/services/interview/evaluation.ts
foundation/euron/apps/api/test/integration/interviews.int.test.ts
foundation/euron/apps/api/test/integration/text-practice.int.test.ts
foundation/euron/apps/api/test/unit/evaluation.test.ts
foundation/euron/apps/stubs/server.mjs
foundation/euron/apps/web/src/components/report/report-body.tsx
foundation/euron/packages/types/src/interview.ts
~~~

### 10.1 Written rubric

The new versioned written-practice rubric contains:

1. domain correctness;
2. depth and reasoning;
3. role relevance and specificity;
4. communication clarity and structure.

### 10.2 Evidence model

The model proposes:

- criterion;
- score or insufficient;
- confidence;
- exact quotations;
- observations tied to evidence indexes.

The model is not trusted to supply the server event ID.

The server itself:

1. loads the authoritative text_practice_events ANSWER event;
2. checks that proposed evidence is an exact substring of that stored answer;
3. binds accepted evidence to the server-owned event ID;
4. rejects/marks unsupported invalid evidence;
5. excludes low-confidence or unsupported findings from aggregate ratings.

### 10.3 Support states

- supported
- uncertain
- unsupported

Supported criteria can affect aggregate scores.

Uncertain/unsupported criteria remain visible but do not silently influence aggregate ratings.

### 10.4 No-answer behavior

No candidate response is stored as:

- domain rating: null;
- communication rating: null;
- explicit explanation that the question was not scored.

This replaces the previous automatic low score.

### 10.5 Provenance

Written feedback records:

- evaluator version;
- rubric version;
- provider ID;
- provider kind;
- model ID;
- model reference;
- simulated status;
- criterion-level evidence/confidence/limitations.

This is stored in the existing feedback JSON structure to avoid an unnecessary migration for the first vertical slice.

### 10.6 Frontend

The report UI displays:

- supported/uncertain/unsupported state;
- proposed score;
- confidence;
- evidence quotation;
- coaching observation;
- limitation;
- provider/rubric provenance.

The UI explicitly warns that evidence authenticity does not prove technical correctness.

## 11. Test evidence for PR #22

Final CI evidence recorded during implementation:

Workflow:
Candidate foundation checks

Run:
43741765689

Environment:

- ubuntu-latest
- Node.js 22
- pnpm 9.15.0
- PostgreSQL 16.12-alpine
- Redis 7.4-alpine

Passed:

- pnpm install --frozen-lockfile
- pnpm audit --prod
- pnpm lint
- pnpm typecheck
- pnpm test
- scripts/test-sanitization.sh
- scripts/check-sanitization.sh
- pnpm test:integration
- pnpm build
- pnpm openapi --check
- make up
- make demo
- pnpm e2e

Observed counts in the final green run:

- 242 unit/component-style tests across non-empty package suites;
- 160 API integration tests across 12 test files;
- 8 Playwright E2E tests;
- production dependency audit reported no known vulnerabilities.

All model/realtime behavior in that CI run used deterministic stubs.

No paid/live provider call was made.

New/updated tests covered:

- fabricated evidence quotation;
- question text incorrectly used as evidence;
- attempted model-supplied/fabricated event reference;
- empty response;
- duplicate criterion;
- structurally contradictory strength/gap claims;
- low-confidence assessment;
- candidate prompt injection;
- malformed provider/model output;
- provider failure;
- evidence ID linked to the actual stored text-practice event;
- spoken response on a coding question not being mislabeled as unanswered.

Important implementation-history note:
CI caught real issues during development. An older integration expectation still asserted 1/100 for an empty answer, and one newly added test initially missed a schema import. Those were fixed before the final green run.

## 12. Recommended final architecture direction

Do not replace the current stack.

Keep:

- Next.js for candidate/admin UI;
- Express/TypeScript API;
- PostgreSQL as the source of truth;
- Redis/BullMQ for background transport/work;
- current typed shared packages;
- current model adapter abstraction.

Add capabilities as modules, not new application stacks.

~~~mermaid
flowchart TB
    UI[Next.js Candidate / Admin UI]
    API[Express API Security Boundary]
    DB[(PostgreSQL Authoritative Data)]
    Queue[(Redis / BullMQ)]
    Jobs[Background Jobs]
    Eval[Rubric + Evidence Validator]
    Adapters[Provider-Neutral LLM Adapters]
    Voice[Realtime Voice Adapters]
    Code[Future Isolated Code Runner]
    Board[Future Whiteboard Persistence]
    Quality[Future Expert / Prompt Regression Harness]

    UI --> API
    API --> DB
    API --> Queue
    Queue --> Jobs
    Jobs --> Adapters
    Jobs --> Eval
    Eval --> DB
    API --> Voice
    API --> Code
    API --> Board
    Quality --> Adapters
    Quality --> Eval
~~~

Suggested future TypeScript responsibilities:

~~~text
foundation/euron/apps/api/src/services/interview/
├── text-practice.service.ts
├── live.service.ts
├── report.service.ts
├── evaluation.ts
├── adaptive-policy.ts
├── follow-up.ts
├── transcript-events.ts
└── session-recovery.ts

foundation/euron/apps/api/src/integrations/
├── llm/
├── realtime/
└── code-runner/
~~~

Do not reorganize the repository just to make it look like this diagram. Create modules only when the next scoped feature needs them.

## 13. Revised 29-gate development sequence

The existing 29 gates remain valuable. They should be executed in dependency order rather than discarded.

### Phase A — Trustworthy feedback

Relevant gates:
10, 11, 17

Sequence:

1. Merge/review evidence-backed written feedback.
2. Build an expert-reviewed synthetic/permitted golden set.
3. Measure scoring agreement, calibration, evidence accuracy and coaching usefulness.
4. Add regression evaluation tooling.
5. Make report/PDF/history consistently expose uncertainty/provenance.

Acceptance:
A score is never treated as validated merely because it was grounded to a quote.

### Phase B — Adaptive written interviews

Relevant gates:
05, 08, 09, 15, 16

Sequence:

1. Formalize authoritative session/turn contracts.
2. Add deterministic coverage/difficulty policy.
3. Add structured follow-up generation.
4. Persist interviewer and candidate events.
5. Add reconnect/recovery and duplicate-request safety.
6. Add competency-level longitudinal analytics.

Acceptance:

- follow-up meaningfully responds to prior answer;
- retries cannot duplicate turns;
- restart/reconnect resumes correctly;
- no second session engine.

### Phase C — Voice

Relevant gates:
09, 12, 24

Sequence:

1. Persist server/provider-authoritative transcript events.
2. Model interruption/barge-in/reconnect semantics.
3. Make voice evidence use authoritative transcript events.
4. Test one authorized real provider.
5. Measure latency, transcription quality, interruptions and cost.
6. Keep deterministic CI stubs.

Acceptance:
Browser display state is not the authoritative transcript.

### Phase D — Coding and system design

Relevant gates:
13, 14, 15, 24

Coding:

1. threat model;
2. self-hosted/vetted isolated runner adapter;
3. deterministic public/hidden tests;
4. resource/time/network limits;
5. AI explanation based on deterministic results.

Whiteboard:

1. Excalidraw integration;
2. persist/reopen board;
3. version board state/events;
4. ground system-design feedback in candidate artifacts.

Acceptance:
No untrusted candidate code executes inside the API or normal application container.

### Phase E — Quality, models and optional fine-tuning

Relevant gates:
17–21

Sequence:

1. baseline evaluation;
2. permitted dataset/provenance;
3. Promptfoo-style regression/red-team;
4. only then QLoRA/SFT experiment;
5. compare fine-tuned model against base;
6. adopt only if measured improvement exists;
7. add vLLM/self-hosting only when economics justify it.

### Phase F — Production, security and later employer workflows

Relevant gates:
22–29

Sequence:

- pricing/quotas/payment;
- deployment/monitoring/backups;
- security/privacy/accessibility review;
- private candidate beta;
- organization tenancy;
- employer assessment validity/fairness/human review;
- ATS/API;
- continuous competitive benchmark.

## 14. Next three development tasks agreed by the audit

### Task 1 — Expert-reviewed scoring benchmark

Objective:
Determine whether grounded model evaluations are technically correct and useful.

Build:

- synthetic/permitted software-engineering answers;
- behavioral answers;
- expert rubric labels;
- evidence annotations;
- clear uncertain/insufficient examples;
- prompt-injection examples.

Measure:

- evidence precision;
- criterion score agreement;
- calibration;
- unsupported-claim rate;
- coaching usefulness;
- expert inter-rater disagreement.

Do not call these grades validated hiring decisions.

### Task 2 — Server-authoritative adaptive written interviewing

Reuse:

- text_practice_sessions;
- text_practice_events;
- version/idempotency infrastructure;
- existing plan;
- existing queue/model adapters;
- DeepInterview policy ideas;
- interview-core invariants.

Acceptance:

- answer-aware follow-up;
- deterministic difficulty/coverage policy;
- persisted interviewer events;
- exact retry/reconnect behavior;
- no duplicate controllers.

### Task 3 — Authoritative voice foundation

Reuse existing realtime adapters.

Change evidence authority:

- persist provider/server transcript events;
- connect voice answers to those events;
- test interruptions/reconnect;
- set duration/quota limits;
- test one authorized real provider;
- retain stub CI.

## 15. Security boundaries

Already present in meaningful form:

- authenticated user ownership;
- server-side authorization;
- rate limiting;
- token/session security;
- provider secret separation;
- prompt fencing;
- structured output schema validation;
- deterministic sanitization checks;
- logging/redaction work;
- explicit consent for text-practice flow.

Still release-critical:

- voice evidence authority;
- secure code sandbox;
- real-provider privacy/retention review;
- candidate deletion/export consistency;
- accessibility review;
- organization tenant isolation for employer mode;
- expert quality validation;
- no sensitive-proxy scoring such as appearance, emotion, accent or protected traits.

## 16. Licensing decisions

### Main repositories

Euron:
MIT. Preserve upstream attribution/license.

DeepInterview:
Apache-2.0. Preserve license and NOTICE obligations if source is copied.

### Important supporting references

LiveKit Agents:
Apache-2.0.

faster-whisper:
MIT source; verify model weights separately.

Piston:
MIT; preferred code-runner candidate after security audit.

Monaco:
MIT; currently unnecessary because CodeMirror already exists.

Judge0:
GPL-3.0; not preferred for proprietary integration without legal review.

Excalidraw:
MIT; preferred whiteboard candidate.

tldraw:
Repository-specific production licensing. Do not assume MIT.

Promptfoo:
MIT.

Langfuse:
MIT core with separately licensed enterprise areas; review exact deployment scope.

Interviewa:
AGPL; research reference unless network-source obligations are intentionally accepted.

Training/model repositories:
Verify both source-code license and each exact model checkpoint license before use.

### Original project licensing

The repository's original code needs an explicit project-license decision before broad commercial distribution/contribution.

Do not assume upstream MIT licensing automatically licenses all original code in this repository.

## 17. Cost strategy

Current CI:
No paid provider required.

Near-term written evaluation:
Keep roughly one structured evaluator call per answered question. Evidence fields increase token use somewhat but do not inherently require a second verifier model call.

Do not add a second model call for every answer until benchmark data shows it is necessary.

Expected variable-cost ordering:

~~~text
text LLM inference
    <
storage / queue infrastructure
    <
isolated code execution
    <
realtime voice STT/LLM/TTS
    <
GPU training / dedicated model serving
~~~

Fine-tuning and GPU hosting are later optimization choices, not prerequisites for an MVP.

## 18. Competitive/product benchmarks

Use only for public feature/UX comparison, not code copying:

- Hello Interview — https://www.hellointerview.com/
- Final Round AI — https://www.finalroundai.com/
- Huru — https://huru.ai/
- Yoodli — https://yoodli.ai/
- CodeSignal — https://codesignal.com/
- HireVue — https://www.hirevue.com/

Benchmark dimensions:

- realism of interview conversation;
- technical correctness of coaching;
- evidence transparency;
- voice latency;
- adaptive follow-ups;
- coding determinism;
- system-design workflow;
- progress/history;
- privacy and controls;
- candidate trust;
- cost per completed session.

## 19. Documentation discrepancies already identified

Older docs contained statements such as:

- Euron has not been imported;
- architecture is only theoretical;
- tests have not been run.

Those statements became stale after the development foundation and text-practice work landed.

PR #22 updates several of them:

- docs/PROJECT_CONTEXT.md
- docs/ARCHITECTURE.md
- docs/QUALITY_AND_TESTING.md
- docs/IMPLEMENTATION_STATUS.md

Future contributors must continue correcting docs when code/test reality changes.

## 20. Important repository documents to read

Mandatory:

- README.md
- AGENTS.md
- REFERENCE_REPOSITORIES.txt
- docs/PROJECT_CONTEXT.md
- docs/VISION.md
- docs/PRODUCT_REQUIREMENTS.md
- docs/ARCHITECTURE.md
- docs/ROADMAP.md
- docs/IMPLEMENTATION_CHECKLIST.md
- docs/IMPLEMENTATION_STATUS.md
- docs/CODEX_BLOCKERS.md
- docs/REUSE_VS_BUILD.md
- docs/LICENSE_AUDIT.md
- docs/QUALITY_AND_TESTING.md
- docs/TEXT_PRACTICE_DEVELOPMENT.md
- docs/decisions/0003-candidate-foundation.md
- foundation/euron/README.md
- CONTRIBUTING.md

This handoff complements those files. It does not replace the source code.

## 21. Reference-repository classifications

### Application-level research

Primary:
- Euron Open Conversation
- DeepInterview

Secondary research only:
- GrillKit
- Interview GPT
- Interviewa
- Local AI Interviewer

### Voice/STT/TTS

- LiveKit Agents
- faster-whisper
- Kokoro 82M

### Model training/inference

- Unsloth
- Unsloth notebooks
- PEFT
- TRL
- vLLM
- Ollama
- llama.cpp
- Qwen checkpoints

### Coding

- Piston
- Monaco
- Judge0

### Whiteboard

- Excalidraw
- tldraw

### Quality/observability/business infrastructure

- Promptfoo
- Langfuse
- Stripe Node

See REFERENCE_REPOSITORIES.txt for the full links and current snapshot notes.

## 22. What future AI/developers must not do

Do not:

- start a new generic AI interviewer repository;
- import another whole Euron copy;
- merge DeepInterview as another app;
- move to Python just because an upstream algorithm is Python;
- create a duplicate auth/database/session system;
- report simulated provider scores as production AI quality;
- claim voice is authoritative while transcript state comes from the browser;
- execute candidate code in the API process;
- start fine-tuning without an evaluation baseline;
- train on scraped/private interview data without rights/provenance;
- deploy publicly or spend money without approval;
- push directly to main unless the repository owner explicitly requests it;
- force-push or destroy history;
- treat exact evidence quotation as proof of score correctness;
- build employer automated hiring decisions from experimental candidate-practice scores.

## 23. How to continue in a fresh ChatGPT/Codex conversation

When a new conversation starts:

1. Give the model the repository URL.
2. Tell it to read AGENTS.md.
3. Tell it to read this MASTER_PROJECT_HANDOFF.md.
4. Tell it to inspect the latest main commit and open PRs.
5. Tell it actual code/tests override old documentation.
6. Tell it not to redo foundation selection.
7. Tell it Euron is the main application and DeepInterview is the intelligence reference.
8. Tell it to continue from the next open development task.
9. Require one scoped branch/PR and real test evidence.
10. Require documentation updates with code.

A ready-to-paste prompt is stored in:
docs/AI_CONTINUATION_PROMPT.md

## 24. Decision summary

~~~mermaid
flowchart TD
    Start[Current AI Interview Repository]
    Euron[Euron-derived TypeScript Application]
    Deep[DeepInterview Research]
    Core[Experimental interview-core]
    Trust[Evidence-backed Written Feedback]
    Adaptive[Adaptive Text]
    Voice[Authoritative Voice]
    Coding[Isolated Coding]
    Board[System Design Whiteboard]
    Eval[Expert Quality Benchmark]
    Model[Optional Fine-tuning / Self-hosting]
    Launch[Secure Candidate Beta]

    Start --> Euron
    Deep --> Adaptive
    Deep --> Eval
    Core --> Trust
    Core --> Adaptive
    Euron --> Trust
    Trust --> Eval
    Eval --> Adaptive
    Adaptive --> Voice
    Adaptive --> Coding
    Adaptive --> Board
    Eval --> Model
    Voice --> Launch
    Coding --> Launch
    Board --> Launch
~~~

## 25. Current recommended immediate action

At this handoff point:

1. Review and merge PR #22 only after human/repository-owner review.
2. Build the expert-reviewed scoring benchmark.
3. Use its results to decide evaluator/prompt improvements.
4. Then implement adaptive written interviewing.
5. Only after that move into authoritative voice and secure code execution.

The project should prioritize trustworthy evaluation over adding more flashy features.

## 26. Durable handoff rule

Every substantial future PR should update:

- docs/IMPLEMENTATION_STATUS.md;
- the relevant subsystem document;
- this master handoff when a major architecture/product decision changes;
- docs/AI_CONTINUATION_PROMPT.md only when the canonical next-task instructions change.

A future AI should be able to continue this project using the repository alone, without access to any previous ChatGPT conversation.
