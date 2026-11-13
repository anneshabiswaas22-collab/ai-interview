# AI Interview — Product and Engineering Handbook

> **Status (13 November 2026): Planning and architecture documentation only. No application code has been imported or implemented in this repository.**
>
> **Mission:** Build an independently branded, self-hostable, commercial-grade AI interviewing platform that can compete with leading interview-preparation products in experience, technical depth, feedback quality, and cost efficiency. Later, support carefully governed employer assessment workflows.

**This repository is the source of truth. A developer or AI coding agent should be able to start here without reading any previous chat.**

## Start here

| You are… | Read these first |
| --- | --- |
| A new developer | [Vision](docs/VISION.md) → [Requirements](docs/PRODUCT_REQUIREMENTS.md) → [Architecture](docs/ARCHITECTURE.md) → [Developer setup](docs/DEVELOPER_SETUP.md) |
| An AI coding agent / Codex | [AGENTS.md](AGENTS.md) → [Reuse vs build](docs/REUSE_VS_BUILD.md) → [Roadmap](docs/ROADMAP.md) |
| An ML engineer | [Interview engine](docs/INTERVIEW_ENGINE.md) → [Models and fine-tuning](docs/MODEL_AND_FINETUNING.md) → [Quality evaluation](docs/QUALITY_AND_TESTING.md) |
| A product contributor | [Feature matrix](docs/FEATURE_MATRIX.md) → [Competitor benchmarks](docs/COMPETITOR_BENCHMARKS.md) |
| A security or legal reviewer | [Security and privacy](docs/SECURITY_AND_PRIVACY.md) → [License audit](docs/LICENSE_AUDIT.md) |

## Product in one minute

The candidate chooses a role and seniority, optionally provides a resume and job description, and practices with a conversational AI interviewer. The interviewer asks context-aware questions, follows up on incomplete answers, and adapts difficulty across behavioral, software engineering, coding, and system-design rounds. Afterward, the candidate receives transcript-backed feedback, strengths, gaps, targeted study recommendations, and longitudinal progress.

**Candidate-first scope:** mock interviews and coaching, not covert assistance during someone else's interview. **Later employer scope:** configurable assessments, reviewer workflows, permissions and auditability — with validated, job-related evaluation and human oversight.

### Competitive references (not an objective market ranking)

- [Hello Interview](https://www.hellointerview.com/) — software engineering, system design, whiteboards and feedback.
- [Final Round AI](https://www.finalroundai.com/) — preparation, personalized interview workflows.
- [Huru](https://huru.ai/) — general interview practice.
- [Yoodli](https://yoodli.ai/) — speaking and communication coaching.
- [CodeSignal](https://codesignal.com/) — technical assessment workflows.
- [HireVue](https://www.hirevue.com/) — enterprise hiring and governance.

See [benchmarks](docs/COMPETITOR_BENCHMARKS.md) for what to research and how to avoid unsupported parity claims.

## Architecture strategy

**One modular monorepo; selective integration of mature open-source components.** Do not copy/merge all upstream applications wholesale.

**Starting application candidate:** [Euron Open Conversation](https://github.com/euron-sde-team/euron-open-real-time-ai-conversation-system) (MIT), **pending a source/security/runtime audit before adoption**. Study [DeepInterview](https://github.com/ngoanpv/DeepInterview) for its interview-agent architecture. Use standard libraries/services only where justified: LiveKit Agents, Piston, Excalidraw, Unsloth, vLLM, Promptfoo and Langfuse.

Important: upstream READMEs describe capabilities, but *we have not yet verified them running in this repository*. Distinguish **verified**, **upstream claimed**, **planned**, **in progress**, and **implemented + tested** in every update.

The solution should eventually provide:
- Candidate web UX, secure accounts, interview scheduling/setup and history
- Role/JD/resume-aware interview preparation and adaptive multi-turn interviewing
- Text/voice interviews with captions, barge-in, latency and cost controls
- A coding editor + **isolated** code execution and tests
- A system-design whiteboard with persisted diagrams and discussion
- Evidence-backed scoring, coach feedback, replay and learning plans
- Provider-neutral AI layer, RAG, original evaluation suite and opt-in fine-tuning
- Admin, quota, analytics and observability, and later employer accounts

See [feature inventory](docs/FEATURE_MATRIX.md) and [technical architecture](docs/ARCHITECTURE.md).

## Development phases and truthful status

| Phase | Goal | Status |
| --- | --- | --- |
| 0 | Document vision, architecture and contributing workflow | Documentation underway |
| 1 | Audit Euron and alternatives; verify licensing, tests and actual working features | Not started |
| 2 | Ship end-to-end text-based candidate practice and feedback | Not started |
| 3 | Production-oriented voice, coding, whiteboard and replay | Not started |
| 4 | LLM evaluations, custom dataset, QLoRA fine-tuning, self-hosted model | Not started |
| 5 | Security, billing, operations and public beta | Not started |
| 6 | Validated employer assessment capabilities | Future; gated |

**Immediate next step:** [Milestone 1: repository audit](docs/ROADMAP.md). Do not write a new interview platform before auditing the foundation.

## Contribution workflow

Read [CONTRIBUTING.md](CONTRIBUTING.md) and the [developer setup guide](docs/DEVELOPER_SETUP.md). Choose a scoped GitHub issue, work on a feature branch, add tests/evidence, and open a PR. AI agents must follow [AGENTS.md](AGENTS.md). Changes affecting the architecture require an ADR.

## Budget and ownership

- Reuse first. Benchmark before fine-tuning; **a fine-tuned smaller model may be worse than a well-prompted base model**.
- Codex Cloud is suitable for coding, repository tasks and testing; GPU model training and production hosting require separately provisioned resources.
- The GitHub repository and all newly written project work can be controlled by the repository owner, but upstream material keeps its original licenses, notices and attribution. **No project's commercial/IP rights are transferred by copying open-source code.**
- Do not upload real resumes, interview audio, candidate PII, credentials or licensed question banks without permission.
- **Licensing of original content in this repository is not yet declared.** Do not assume public GitHub visibility equals an open-source license; maintainers should establish a contribution and licensing policy before external code contributions.

## Documentation index

- **Product:** [Vision](docs/VISION.md), [Requirements](docs/PRODUCT_REQUIREMENTS.md), [Competitor benchmarks](docs/COMPETITOR_BENCHMARKS.md), [Feature matrix](docs/FEATURE_MATRIX.md)
- **Engineering:** [Architecture](docs/ARCHITECTURE.md), [Interview engine](docs/INTERVIEW_ENGINE.md), [API contracts](docs/API_CONTRACTS.md), [Data model](docs/DATA_MODEL.md), [Voice/coding/whiteboard](docs/VOICE_CODING_WHITEBOARD.md)
- **AI/quality:** [Model & fine-tuning](docs/MODEL_AND_FINETUNING.md), [Testing & evaluation](docs/QUALITY_AND_TESTING.md)
- **Execution:** [Roadmap](docs/ROADMAP.md), [Reuse vs build](docs/REUSE_VS_BUILD.md), [Credit efficiency](docs/CREDIT_OPTIMIZATION.md), [Developer setup](docs/DEVELOPER_SETUP.md), [AI agent instructions](AGENTS.md)
- **Governance:** [Security & privacy](docs/SECURITY_AND_PRIVACY.md), [License audit](docs/LICENSE_AUDIT.md), [Architecture decisions](docs/decisions/0001-monorepo-reuse-first.md)

_This is a project blueprint, not a claim of an already deployed product. Last reviewed: 2026-11-13._
