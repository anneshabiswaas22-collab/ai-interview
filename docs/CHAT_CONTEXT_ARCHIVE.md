# Conversation Context Archive — AI Interview Platform

Last consolidated: 2026-11-16

## Purpose

This file preserves the important owner instructions and conclusions from the long AI Interview Platform discussion so future AI/developers do not need access to the original ChatGPT thread.

It is not intended as a word-for-word log of every tool status update. It preserves the substantive requests, constraints, architecture decisions, audit findings and implementation outcomes.

If this file conflicts with current source code or recent executed tests, source/tests win.

## A. Owner's core request

The repository is the source of truth:

https://github.com/anneshabiswaas22-collab/ai-interview

The owner asked the assistant to act as:

- Principal Software Architect
- Senior Full-Stack Engineer
- AI/ML Architect
- Code Reviewer
- Technical Research Lead

The objective is to improve and extend the existing repository into an independently branded, self-hostable, commercially competitive AI interview-preparation product.

The owner explicitly said:

- do not generate another generic AI interviewer;
- do not start a new project;
- inspect actual implementation before decisions;
- research deeply;
- do not stop at README files;
- inspect source, tests, dependencies, migrations, workflows and architecture;
- verify important claims;
- do not invent explanations;
- explain tradeoffs;
- do not make the project unnecessarily complicated;
- reuse working code;
- do not spend money;
- do not expose secrets;
- do not deploy publicly;
- do not make destructive repository changes without approval.

## B. Mandatory repository reading requested by the owner

The owner requested inspection of at least:

1. README.md
2. AGENTS.md
3. REFERENCE_REPOSITORIES.txt
4. docs/PROJECT_CONTEXT.md
5. docs/VISION.md
6. docs/PRODUCT_REQUIREMENTS.md
7. docs/ARCHITECTURE.md
8. docs/ROADMAP.md
9. docs/IMPLEMENTATION_CHECKLIST.md
10. docs/IMPLEMENTATION_STATUS.md
11. docs/CODEX_BLOCKERS.md
12. docs/REUSE_VS_BUILD.md
13. docs/LICENSE_AUDIT.md
14. docs/QUALITY_AND_TESTING.md
15. docs/TEXT_PRACTICE_DEVELOPMENT.md
16. docs/decisions/0003-candidate-foundation.md
17. foundation/euron/README.md
18. CONTRIBUTING.md

The owner explicitly warned that some planning documents can be outdated and that actual source code plus recent verified tests should be authoritative.

The owner also explicitly said not to restart the old foundation-selection task simply because an older kickoff file says to do so.

## C. Repository architecture context established

The repository already includes:

- an adapted Euron application under foundation/euron;
- an experimental policy/evidence package under packages/interview-core.

The desired end state is one authoritative interview engine, not duplicate session controllers.

Current development stack:

- Next.js frontend
- Express/TypeScript API
- PostgreSQL
- Redis/BullMQ
- provider-neutral LLM adapters
- realtime provider adapters
- deterministic provider stubs
- shared TypeScript contracts
- GitHub Actions validation

## D. Reference-repository research request

The owner asked that REFERENCE_REPOSITORIES.txt be read fully and that relevant public repositories be studied for:

- real code architecture;
- documentation;
- licenses;
- maintenance risk;
- feature overlap;
- security;
- integration cost;
- operating cost;
- long-term ownership.

The owner required EXACTLY TWO main application-level repositories.

Leading candidates named by the owner:

### Candidate A — Euron Open Conversation

https://github.com/euron-sde-team/euron-open-real-time-ai-conversation-system

Expected role:
Primary application foundation.

Requested investigation included:

- Next.js frontend;
- Express backend;
- authentication/authorization;
- PostgreSQL schema/migrations;
- Redis/BullMQ;
- interview creation/planning;
- resume/JD processing;
- model adapters;
- text/voice interview flows;
- reports/scoring/history;
- security/testing/deployment.

The owner explicitly said:
Do not copy another entire Euron instance into the repository.

### Candidate B — DeepInterview

https://github.com/ngoanpv/DeepInterview

Expected role:
Secondary interview-intelligence reference.

Important source areas named by the owner:

- apps/agent/src/deepinterview_agent/prep/
- apps/agent/src/deepinterview_agent/live/
- apps/agent/src/deepinterview_agent/post/

Requested research included:

- resume/JD-aware preparation;
- planning;
- multi-agent orchestration;
- conversational follow-ups;
- adaptive difficulty;
- competency scoring;
- evaluation verification;
- lifecycle management;
- voice limits/interruptions;
- coaching.

The owner explicitly said:
Do not merge DeepInterview as a second application.

## E. Final two-repository conclusion

The research concluded the best two main application-level repositories/references are:

### 1. Euron Open Conversation

URL:
https://github.com/euron-sde-team/euron-open-real-time-ai-conversation-system

Role:
Primary application foundation.

Verified revision during research:
216a8fc52a055587f436f2446f1a80b6868bd14a

License:
MIT.

Reason:
Already adapted into the repo and provides the most compatible platform foundation.

### 2. DeepInterview

URL:
https://github.com/ngoanpv/DeepInterview

Role:
Interview-intelligence and architectural reference.

Verified revision during research:
bd6d136fffc509265bc2355e95101e0ad7f56eac

License:
Apache-2.0.

Reason:
Strong adaptive interviewing/evaluation ideas, but importing its Python application would create an unnecessary second stack.

The short user-facing summary was:

Euron = main codebase.
DeepInterview = intelligence/design reference.

## F. Other repository classifications

The discussion explicitly classified other full interview applications as research/alternatives rather than main foundations:

- GrillKit
- Interview GPT
- Interviewa
- Local AI Interviewer

Component/reference categories discussed:

Voice/STT:
- LiveKit Agents
- faster-whisper
- Kokoro

Training/inference:
- Unsloth
- Unsloth notebooks
- PEFT
- TRL
- vLLM
- Ollama
- llama.cpp
- Qwen checkpoints

Coding:
- Piston
- Monaco
- Judge0

Whiteboard:
- Excalidraw
- tldraw

Quality/observability:
- Promptfoo
- Langfuse

Payments:
- Stripe Node

Proprietary benchmarks:
- Hello Interview
- Final Round AI
- Huru
- Yoodli
- CodeSignal
- HireVue

Full maintained links live in REFERENCE_REPOSITORIES.txt.

## G. Architecture audit requested by owner

The owner required a real code audit of:

Frontend:
foundation/euron/apps/web/src/

Backend:
foundation/euron/apps/api/src/

Database:
foundation/euron/db/migrations/

Experimental core:
packages/interview-core/

The owner asked to identify:

1. architecture strengths;
2. major weaknesses;
3. code-supported bugs/suspicious behavior;
4. missing security controls;
5. duplicated responsibilities;
6. missing tests;
7. scaling bottlenecks;
8. unnecessary dependencies;
9. stale documentation;
10. highest-value improvements.

The owner required important findings to reference exact repository paths/functions/lines and to distinguish confirmed problems from potential risks.

## H. Key audit findings preserved from the discussion

Confirmed strengths included:

- substantial Euron application already integrated;
- real auth/database/dashboard/report infrastructure;
- provider-neutral model resolution;
- schema-validated structured model calls;
- deterministic stub providers;
- server-authoritative written text practice;
- request replay/idempotency/versioning for written practice;
- durable score dispatch/outbox;
- broad unit/integration/browser tests.

Confirmed weaknesses included:

### Empty answers were automatically scored as failures

Before the evidence PR, legacy scoreAnswer logic could force an unanswered response to 1/100.

The project decision:
No response should be unscored/insufficient, not automatically incorrect.

### Written scoring lacked server-validated evidence

Legacy model output contained scores/prose without proving that claims referred to actual stored candidate responses.

The project decision:
The model can propose evidence, but the server must validate it against authoritative records.

### Voice transcripts are not yet authoritative enough

The frontend live room can send browser-held transcript state back to the API.

The project decision:
Future voice evaluation should use server/provider-persisted transcript events.

### Coding is not secure deterministic execution yet

The application has a browser editor but no isolated production code runner.

The project decision:
Use a future isolated runner, with Piston as preferred candidate after security review.

### Evidence provenance does not prove technical correctness

The project decision:
A quote being authentic only proves provenance. Expert-reviewed quality evaluation is still required.

### Written practice currently follows a fixed plan

The project decision:
Add adaptive follow-ups later using server-authoritative session events and deterministic coverage/difficulty policy.

### Experimental interview-core must not become a second engine

The project decision:
Port useful invariants into the production TypeScript path and avoid parallel controllers.

## I. First implementation task requested by owner

The owner selected the first high-value vertical slice:

Evidence-backed feedback for existing written interview practice.

Requested behavior included:

1. explicit job-relevant competency rubrics;
2. evaluation claims tied to candidate evidence;
3. server validation of evidence references;
4. supported vs uncertain vs unsupported findings;
5. no invented evidence/scores/accomplishments;
6. preserve report structure where practical;
7. record provider/model provenance and distinguish mocks;
8. safe malformed-output/provider failure handling;
9. no automatic failure for unanswered questions;
10. actionable technical suggestions;
11. compatible migrations or properly tested changes;
12. show evidence/uncertainty/limitations in frontend;
13. reuse auth/queues/retries;
14. tests for fabricated evidence, bad references, empty answers, contradictory claims and prompt injection.

The owner also explicitly stated:
Verifying that a quotation appears in the transcript does not prove the technical correctness of a score.

## J. Implementation completed during the discussion

A branch was created:

feat/evidence-backed-text-feedback

A pull request was opened:

https://github.com/anneshabiswaas22-collab/ai-interview/pull/22

At handoff:

- PR #22 was open;
- ready for review;
- not merged;
- mergeable;
- base main commit was 08af53c16753bd8a3e580de32760a9c02e5def60;
- head was 13b9db99b4f6d4c911e6c43337d4fc656db4f595.

The implementation added a written evaluation contract with:

- versioned rubric;
- exact candidate-answer quotations;
- server-bound evidence event IDs;
- supported/uncertain/unsupported states;
- low-confidence exclusion from aggregate scores;
- no-response = null/unscored;
- provider/model/rubric provenance;
- limitations displayed in the report UI.

Important:
This implementation validates evidence provenance, not technical truth.

## K. PR #22 test evidence recorded in the discussion

Final green GitHub Actions environment:

- ubuntu-latest
- Node.js 22
- pnpm 9.15.0
- PostgreSQL 16.12-alpine
- Redis 7.4-alpine

Passed commands:

- pnpm install --frozen-lockfile
- pnpm audit --prod
- pnpm lint
- pnpm typecheck
- pnpm test
- bash scripts/test-sanitization.sh
- bash scripts/check-sanitization.sh
- pnpm test:integration
- pnpm build
- pnpm openapi --check
- make up
- make demo
- pnpm e2e

Observed totals:

- 242 unit/component tests across non-empty suites;
- 160 API integration tests;
- 8 Playwright E2E tests.

All model/realtime calls in this CI were deterministic stubs.

No paid/live provider call occurred.

The CI process itself found and helped correct two issues during development:

- an old test expected empty answers to score 1/100;
- a newly added test temporarily omitted a schema import.

Only the final green head should be treated as successful evidence.

## L. Architecture direction agreed in discussion

Keep the current stack.

Frontend:
Next.js.

Backend:
Express/TypeScript.

Authoritative storage:
PostgreSQL.

Background transport:
Redis/BullMQ.

AI:
Provider-neutral adapters.

Voice:
Existing realtime adapters first; add components only if justified.

Code:
Separate isolated execution service in a future phase.

Whiteboard:
Excalidraw is the preferred future candidate.

Evaluation:
Separate typed rubric/evidence validation module.

Do not reorganize the entire repository merely to match a theoretical diagram.

## M. Development phase order agreed in discussion

### Phase A
Evidence-backed scoring and trustworthy reports.

### Phase B
Genuinely adaptive text interviews and authoritative session recovery.

### Phase C
Real voice, transcription and interruption handling.

### Phase D
Secure coding assessment and persistent system-design whiteboard.

### Phase E
Quality evaluation, permitted datasets, optional fine-tuning and cost optimization.

### Phase F
Security hardening, operations, beta release and later employer workflows.

Avoid premature microservices and unnecessary model training.

## N. Immediate next three tasks agreed

1. Build expert-reviewed scoring benchmark.
2. Build server-authoritative adaptive written interviewing.
3. Make voice transcript events server-authoritative and production-testable.

## O. Owner's continuity request

After the audit/implementation discussion, the owner explained that long ChatGPT conversations become difficult to reload and can create continuity problems.

The owner requested that:

- all important research;
- documents;
- charts;
- links;
- architecture;
- implementation findings;
- conversation decisions;
- development status

be pushed into the GitHub repository.

Reason:
A future ChatGPT/Codex session should be able to continue the project from GitHub without needing the old conversation.

This archive, MASTER_PROJECT_HANDOFF.md, RESEARCH_AND_REPOSITORY_DECISIONS.md and AI_CONTINUATION_PROMPT.md were created specifically to satisfy that continuity requirement.

## P. Rule for future conversations

Do not ask the owner to reconstruct this old conversation.

Instead:

1. inspect the repository;
2. read AGENTS.md;
3. read docs/MASTER_PROJECT_HANDOFF.md;
4. read docs/RESEARCH_AND_REPOSITORY_DECISIONS.md;
5. read docs/AI_CONTINUATION_PROMPT.md;
6. inspect latest main/open PRs;
7. continue from actual code/test state.
