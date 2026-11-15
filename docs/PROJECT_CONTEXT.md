# Complete Project Context — Independent Handoff

**Purpose:** A new contributor, an AI coding agent or a future owner can understand the entire project from GitHub without the original ChatGPT conversation.

## Original owner objective

Create an independently branded, commercially competitive **AI interviewer software system**. The objective is not a demo, shallow questionnaire or simple fork. The desired platform should eventually compete with the strongest existing AI interview-preparation and assessment products in their respective specialties. There is no verified single worldwide "#1" product, so the correct approach is a multi-product benchmark.

## Why this repository exists

The owner wants:
- **Full control** of the new product code, data, prompts, model adapters, infrastructure and brand under their GitHub account, while honoring third-party licenses.
- **Codex Cloud / GPT-6 Astra** to implement and test scoped development milestones against the GitHub repository.
- **Mature open-source reuse** to avoid spending model credits reimplementing authentication, voice transport, editor, whiteboard, model training and observability.
- **One final owned monorepo**, not several disconnected apps and not a naive source merge.
- **A custom fine-tuned open-weight interviewer** after establishing that data, evaluation and infrastructure support it; GPU training may be done in Google Colab or another authorized external GPU environment.
- **A product roadmap** from candidate practice to potential employer workflows, with strong technical interviews, natural conversations, cost controls and professional user experience.

## Decisions from earlier planning

1. Candidate-first product: interview setup, resume and job context, technical/behavioral/coding/system-design interviews, transcripts, evidence-based feedback and history.
2. Candidate practice product benchmarks: Hello Interview, Final Round AI, Huru, Yoodli; future assessment benchmarks: CodeSignal and HireVue.
3. **Preferred first foundation to audit:** Euron Open Conversation, because its published description includes accounts, voice, plans, reports, admin and quotas. Adoption is conditional on verifying reality/security.
4. **Reference architecture to study:** DeepInterview for conversational orchestration, mock-vs-live providers and interview lifecycle; GrillKit for coding/reusable question patterns.
5. **Selectively integrate mature packages:** LiveKit Agents, Piston, Excalidraw, Promptfoo, Langfuse, Unsloth, vLLM; do not import any wholesale without reason.
6. **Don't retrain from scratch.** Start from a checkpoint-specific, license-verified Qwen-family model and baseline. Fine-tune with QLoRA using original, permitted multi-turn interview data only when it improves held-out metrics.
7. **Do not spend on large-scale infra before product validation.** Keep a working basic text session first, then add voice/coding/whiteboard, then model optimization and commercial infrastructure.
8. Engineering work goes via small documented commits/PRs and tests. Preserve unmodified upstream license notices.

## Important truth as of 2026-11-15

The repository now contains an adapted, pinned Euron development foundation under [foundation/euron](../foundation/euron/README.md), plus the earlier dependency-free [interview-core](../packages/interview-core/README.md) prototype. The imported application has working authentication/database/UI/job infrastructure and a consent-based server-authoritative **text-practice** path with clean-checkout CI evidence using simulated providers. It is still a development preview: real-provider model quality, production voice, secure code execution, public deployment, fine-tuning and release security/compliance have not been validated. The experimental core is not a second production session engine.

## Technical vision

- Web: responsive, polished candidate dashboard, accessible setup, timed interview room, replay and reports.
- Backend: authenticated API, session orchestration, event persistence, quotas, role-based authorization.
- AI: contextual planning, follow-up state machine, RAG, model adapters, independent evaluator with evidence references.
- Technical: real code editor and isolated execution with deterministic tests, saved system-design board and diagram discussion.
- Voice: responsive STT/LLM/TTS pipeline with interruptions, captions and optional recording consent.
- ML: tested original dataset, baselines, QLoRA training, model cards, rollback and external GPU execution.
- Ops: security/privacy, secrets, backups, observability, unit economics and CI.

The selected development direction is the existing **Next.js + Express + PostgreSQL + Redis Euron foundation**, extended in place. Major stack changes still require evidence and an ADR; do not create a parallel application stack.

## Priority and handoff

1. Start with [implementation status](IMPLEMENTATION_STATUS.md) and the next open gate; the original Euron foundation-selection audit has already produced ADR 0003 and an imported development candidate.
2. Follow [AGENTS.md](../AGENTS.md) for Codex and [CONTRIBUTING.md](../CONTRIBUTING.md) for human contributors.
3. Read [Feature Matrix](FEATURE_MATRIX.md), [Roadmap](ROADMAP.md), [Architecture](ARCHITECTURE.md), [Reuse vs Build](REUSE_VS_BUILD.md), [License Audit](LICENSE_AUDIT.md).
4. Contribute one real, testable vertical slice at a time, recording exact failures/skips and remaining limitations.

## Open decisions

- How and when the provisional Euron development foundation graduates to a production-approved base.
- Schema evolution for authoritative adaptive sessions, evidence-backed evaluation, voice and later organization tenancy.
- Model checkpoint, providers and measured serving costs.
- Product name, visual brand, business incorporation and original-code licensing/contribution terms.
- Jurisdiction-specific privacy, payments and employer assessment obligations.
- Provider selection for local vs managed voice and deployments.

These decisions are intentionally open; no developer should guess they were finalized in a private chat.
