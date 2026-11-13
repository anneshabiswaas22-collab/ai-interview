# System Architecture — Proposed, Not Yet Implemented

**Architecture status: design target.** The Euron repository is a *candidate* application foundation, not yet imported. Its documented stack is Next.js + Express + PostgreSQL + Redis. Confirm it by source/runtime audit before adopting a different stack.

## Design goals

- One repository, modular boundaries; independent services only when isolation or scaling justifies them.
- No duplicated auth, queues, code editors, model clients or session databases.
- Own our interview orchestration and evaluation logic; swap hosted/local AI providers.
- Privacy by default, observable costs and quality, deterministic grading where possible.
- Easy contributor onboarding and incremental PRs.

## High-level target

\`\`\`mermaid
flowchart TB
  C[Candidate web app] --> API[Authenticated API / BFF]
  A[Admin web UX] --> API
  API --> DB[(PostgreSQL)]
  API --> OBJ[(Encrypted object storage)]
  API --> QUEUE[(Redis / job queue)]
  API --> ORCH[Interview orchestrator]
  ORCH --> LLM[LLM provider adapter]
  ORCH --> EVA[Rubric evaluator]
  ORCH --> RAG[Authorized retrieval context]
  C <-->|WebRTC| VOICE[Realtime voice agent]
  VOICE --> LLM
  VOICE --> STT[Speech-to-text adapter]
  VOICE --> TTS[Text-to-speech adapter]
  API --> CODE[Restricted code-execution service]
  API --> BOARD[Whiteboard state]
  QUEUE --> EVA
  API --> OBS[Redacted traces, logs & metrics]
  ORCH --> OBS
  EVA --> OBS
\`\`\`

Diagram shows a target architecture, **not deployed services**.

## Proposed monorepo layout

Maintain/reshape after Euron audit; do not delete working upstream code simply to match folder names:

\`\`\`text
ai-interview/
  apps/
    web/                 # candidate and admin UI, Next.js or chosen framework
    api/                 # authenticated public API, authorization, orchestration boundary
  services/
    interviewer/         # FSM, follow-up policy, context windows
    evaluation/          # rubric scorer, evidence attribution
    voice/               # realtime transport/worker, STT/TTS adapters
    code-runner/         # isolated execution proxy (not arbitrary server eval)
    inference/           # OpenAI-compatible provider adapter/service
  packages/
    contracts/           # versioned TypeScript schemas / OpenAPI
    ui/                  # accessible design components
  ml/
    datasets/            # synthetic/permissioned samples, manifests, no candidate data
    training/            # Unsloth/TRL scripts + Colab notebook
    evaluation/          # golden dialogs, grader criteria, runs
  infrastructure/        # compose, IaC, secrets templates
  docs/                  # engineering source of truth
  tests/                 # E2E, integration, performance, adversarial
  AGENTS.md
\`\`\`

Actual directories do not yet exist. Contributors should not claim they do.

## Responsibilities

**Web:** setup, resume/JD submission, voice/text UI, editor, whiteboard, transcript and reports. Never trusts scores or system prompts provided by the browser.

**API/BFF:** identity, tenant authorization, uploads/validation, quota and cost limits, short-lived realtime tokens, session versioning, event persistence and pagination.

**Interview orchestrator:** pinned interview plan; choose next question/probe; max follow-ups and time budget; detect repetition; transition using typed state; retain explicit provenance for context. Candidate text is *untrusted content*, not a system instruction.

**Model adapter:** providers exposed through versioned \`generateStructured\` / \`stream\` contracts; retries bounded; explicit timeout, tokens and unit costs; fail closed when provider unavailable. Do not introduce multiple orchestration frameworks without measured need.

**Evaluator:** operates outside the live interview turn loop, reads immutable events, scores competency rubrics and links evidence. Code correctness comes from sandbox tests, not AI opinion alone.

**Voice:** LiveKit/WebRTC transport, STT/TTS provider modules, interruption/barge-in semantics; use natural turn detection and synchronized transcript events; optional audio recording with separate consent.

**Coding:** restrict all candidate code execution to self-hosted Piston or equivalent audited executor behind a network-isolated proxy; never execute in API container. Test limits for time, memory, PIDs, output and egress.

**Whiteboard:** Excalidraw board state managed as versioned objects; AI comments on *technical content* only, not visual polish.

**Analytics:** OpenTelemetry tracing with redaction and optional Langfuse. Record provider latency, errors, token/voice consumption; no raw resumes or keys in logs.

## Interview lifecycle

\`\`\`mermaid
sequenceDiagram
  actor User as Candidate
  participant Web
  participant API
  participant Planner
  participant Agent as Interview agent
  participant Score as Evaluator
  User->>Web: Select role / optionally provide resume
  Web->>API: Create draft interview + consent
  API->>Planner: Produce job-relevant plan
  Planner-->>API: Validated plan + rubric
  API-->>Web: Session and plan overview
  User->>Web: Start session
  Web->>API: Start authenticated interview
  loop Questions and bounded follow-ups
    User->>Web: Answer (text or speech)
    Web->>API: Append event with idempotency key
    API->>Agent: State + evidence + remaining time
    Agent-->>Web: Question / follow-up / close
  end
  User->>API: End session
  API->>Score: Evaluate immutable transcript
  Score-->>API: Rubric scores and cited evidence
  API-->>Web: Report, coaching and history
\`\`\`

## Security boundaries

- API is authoritative for permissions, duration, quotas, interview completion and grading.
- Candidate inputs, uploaded documents, web retrieval and model output are untrusted.
- Strict validation with typed schemas; human-friendly error handling; limited context injection.
- Protect against cross-user and cross-tenant access, replayed events, tool abuse, prompt injection and SSRF.
- Consent before audio recording; transcript, code and whiteboard retention managed separately.
- No automatic employer hiring decisions.

## Performance and reliability

Measure rather than promise. Establish p50/p95 streaming latency, voice interruption time, failed-turn rates, inference costs and long-session memory growth. Add retry/reconnect, idempotency and degraded text fallback. Scale only after load tests.

## Key ADRs

- [ADR-0001 — Modular monorepo and reuse-first](decisions/0001-monorepo-reuse-first.md)
- [ADR-0002 — Candidate-first, evidence-based scoring](decisions/0002-candidate-first-evaluation.md)

See [API contracts](API_CONTRACTS.md), [data model](DATA_MODEL.md), [security](SECURITY_AND_PRIVACY.md).
