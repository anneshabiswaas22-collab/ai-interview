# Preserved Source Inventory and Adoption Analysis

Reviewed: 17 November 2026. This is a static source review. Archived programs were not executed, and upstream claims are not local verification.

## Decision summary

Keep `foundation/euron` as the only runnable development candidate. Preserve all four extracted projects here for provenance and future analysis. Adopt ideas or small components only after a dedicated architecture decision, license review, threat model, and tests. Do not concatenate complete applications.

## DeepInterview

Path: `sources/DeepInterview-main/`

- License: Apache-2.0 with `LICENSE` and `NOTICE`; retain both and mark modified copied files.
- Stack: Next.js/React/TypeScript web, Python/FastAPI/LangGraph agent, LiveKit, optional Supabase/R2, and an optional Python RAG sidecar.
- Valuable ideas: prep/live/post boundaries, provider adapters, bounded interview turns, transcript checkpoints, scoring verifier, question skill packs, local-provider seams, and cross-language contract parity.
- Material risks: it is a second complete application; self-host defaults can disable authentication; some trace and session access relies on weak capability assumptions; resume retrieval/parser paths need stronger SSRF, size, and isolation controls; optional containers/models are not sufficiently pinned for production.
- Disposition: research only. Reimplement or adapt narrowly selected patterns behind the existing Euron authentication, database, and server-owned evaluation contracts.

## Euron upstream snapshot

Path: `sources/euron-open-real-time-ai-conversation-system-main/`

- License: MIT; retain the ENGAGESPHERE/Euron copyright and license notice.
- Pinned source: archive identifies commit `216a8fc52a055587f436f2446f1a80b6868bd14a`, matching the upstream base already used by `foundation/euron`.
- Stack: TypeScript monorepo with Next.js, Express, PostgreSQL, Redis/BullMQ, model and realtime adapters, shared packages, Docker, Terraform, Vitest, and Playwright.
- Current relationship: most of this source duplicates the existing foundation. The current foundation intentionally adds text practice, transactional score dispatch, provider/source labeling, updated Zod, consent corrections, migrations, and tests.
- Material risks: upstream voice transcripts and proctoring remain browser-authored/advisory; model scores are not sufficient evidence; code is not safely executed; real-provider quality, cost, privacy, accessibility, and security remain unapproved.
- Disposition: provenance/reference snapshot only. Never replace the adapted foundation wholesale with this older upstream tree.

## GrillKit

Path: `sources/grillkit-main/`

- License: Apache-2.0 with `LICENSE` and `NOTICE`; question-content provenance still requires a separate audit.
- Stack: Python 3.12, FastAPI/WebSockets, SQLAlchemy/SQLite, Jinja/JavaScript, OpenAI-compatible LLM, Whisper, Piper, and optional Judge0.
- Valuable ideas: theory/coding phase orchestration, stable question taxonomy, known-question tracking, public/hidden tests, attempt history, deterministic code outcomes, timers, and speech readiness UX.
- Material risks: designed for one local user with no hosted authentication or tenant isolation; plaintext local keys; user-configured server URLs can create SSRF; bundled Judge0 uses privileged containers and development credentials; only Python execution is mapped; prompt injection and content provenance need deeper review.
- Disposition: research only. Consider schemas and workflows, but place any future code execution behind a separately hardened, network-restricted service.

## Local AI Interviewer

Path: `sources/local-ai-interviewer-main/`

- License: MIT; retain the author copyright and license notice.
- Stack: React/TypeScript/Vite frontend, Python/FastAPI/Pydantic backend, SQLite, local Ollama, optional cloud Ollama, optional Whisper, document parsing/OCR, and ReportLab.
- Valuable ideas: compare-and-set interview transitions, replay protection, answer-before-evaluation persistence, schema-validated and evidence-linked scoring, pure adaptive-policy functions, resume claim traceability, local/cloud consent, budget tracking, and redacted exports.
- Material risks: single-user loopback security model; no tenant isolation; cloud keys may be stored in plaintext SQLite; synchronous/local persistence conflicts with the hosted architecture; real-model grading, cloud, microphone, accent, and device behavior are not established by mocked tests.
- Disposition: high-value reference implementation. Port small dependency-light algorithms to TypeScript with parity tests, or isolate a narrowly scoped Python ML service only when its ecosystem value justifies the operational boundary.

## Language strategy

Do not translate every source into one language merely to make the repository look uniform.

- Use TypeScript for the primary web application, API, contracts, session policy, reports, and most product logic.
- Use Python only for isolated ML, speech, dataset, evaluation, or training workloads where the Python ecosystem provides clear measured value.
- Communicate through versioned OpenAPI/JSON Schema contracts and bounded job/event interfaces.
- Keep PostgreSQL authoritative and reuse the existing Redis queue.
- Never create a second authentication system, session engine, UI, or primary database from an archived project.

## Priority adoption candidates

1. Evidence-linked evaluator rules and deterministic consistency checks.
2. Server-owned, persisted state transitions and replay-safe retries.
3. Question taxonomy with source/provenance fields and known-question tracking.
4. Provider cost budgets, consent, and local/hosted routing contracts.
5. Transcript checkpoints and reliable reconnect behavior.
6. Isolated code-execution adapter whose deterministic tests outrank model judgment.
7. Accessible voice readiness, captions, and text fallback.

Each candidate remains planned until implemented and tested in the authoritative application.
