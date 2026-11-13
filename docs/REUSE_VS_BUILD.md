# Reuse vs Build — Credit-Saving Integration Strategy

_Date checked: 2026-11-13 for GitHub repository existence/metadata; source test results **not yet verified**._

## Decision rule

**Reuse mature, correctly licensed, working functionality. Build only our differentiators.** Each proposed integration must pass these gates: feature fit → license → source audit → tests → security → integration cost → ongoing maintenance. An SDK or separately deployed service is preferable to copying a large unrelated app.

| Layer | Candidate | Integration mode | Decision / caution |
| --- | --- | --- | --- |
| Product foundation | [Euron Open Conversation](https://github.com/euron-sde-team/euron-open-real-time-ai-conversation-system) | Inspect as starting application | **Candidate base**, MIT, audit first; README describes accounts, plans, voice, reports, admin, test suite |
| Interview agent design | [DeepInterview](https://github.com/ngoanpv/DeepInterview) | Study/adapt compatible components | Apache 2.0; README calls project an **early build** and distinguishes mock adapters from live voice |
| Technical interview examples | [GrillKit](https://github.com/Forkfield/grillkit) | Reference for editor, tracks, question packs | Its LICENSE file declares Apache 2.0; code depends on Judge0 for coding; verify content rights and dependencies |
| Voice transport | [LiveKit Agents](https://github.com/livekit/agents) | Official SDK/service | Apache 2.0; host or use managed service with explicit cost accounting |
| Speech recognition | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Optional local adapter | Confirm checkpoint model licenses and GPU needs before selecting |
| Speech generation | [Kokoro](https://huggingface.co/hexgrad/Kokoro-82M) or another provider | Model-backed adapter | Confirm weight license, quality, language, redistribution and voice rights |
| Browser code editor | Existing Euron editor first; [Monaco](https://github.com/microsoft/monaco-editor) if gap | Embed UI package | Avoid replacing an editor without clear functional reason |
| Code execution | [Piston](https://github.com/engineer-man/piston) | **Self-hosted isolated service** | MIT; public hosted API must not be assumed available; review sandbox/egress controls |
| Design whiteboard | [Excalidraw](https://github.com/excalidraw/excalidraw) | Embedded package | MIT; persist board state; build only interview-specific feedback |
| Prompt/model testing | [Promptfoo](https://github.com/promptfoo/promptfoo) | Test/dev dependency | MIT; integrate golden scenarios into CI |
| LLM observability | [Langfuse](https://github.com/langfuse/langfuse) | Optional self-hosted service | Core MIT, enterprise directories separately licensed; make redaction default |
| Fine-tuning | [Unsloth](https://github.com/unslothai/unsloth), Hugging Face PEFT/TRL | Training dependency | Unsloth core Apache 2.0; review optional Studio packages separately |
| Inference | [vLLM](https://github.com/vllm-project/vllm), Ollama or compatible endpoint | Replaceable provider service | vLLM Apache 2.0; self-hosting incurs GPU cost |
| Database | PostgreSQL (foundation) | Keep existing schema/migrate carefully | Do not add a separate DB for every service |
| Background jobs | Existing Redis queue if audited | Keep foundation | Don't mix multiple queue stacks without requirement |
| Billing | Official provider SDK later | Service integration | Payments/licensing/eligibility differ by region |
| User analytics | Existing event capture/OpenTelemetry first | Lightweight integration | Don't introduce expensive data stack before use |

## What we should **not** clone or merge by default

- Euron + DeepInterview + GrillKit as three complete deployable apps. This duplicates auth, UI, database, packages and CI.
- tldraw as an assumed free production whiteboard; review its production/commercial SDK license before considering.
- Judge0 under a "no-cost no-license obligations" assumption (its GPL terms require review).
- A second authentication solution when Euron's auth passes review.
- An avatar/video-generation stack before realistic text/voice interviewing works.
- Generic CRM, complex subscriptions and analytics warehouse before candidate value is proven.

## Reuse decision record template

For every component PR include:
1. Existing solution and observed version/commit.
2. Build vs reuse alternatives and rough integration effort.
3. License, NOTICE and dependency/SBOM obligations.
4. Security findings and data flows; internet access or file-system requirements.
5. Real tests executed, known mocks and performance measured.
6. How to remove, upgrade or replace the component.
7. Total expected operating cost, not only development time.

## Cost-saving sequencing

1. Audit existing Euron functionality before touching it.
2. Keep UI/auth/report/quotas if serviceable.
3. Make one *real* text interview end-to-end.
4. Add Promptfoo and tracing to measure quality/price.
5. Integrate Piston/Excalidraw/LiveKit in bounded PRs.
6. Fine-tune only after base-vs-fine-tuned evaluation identifies a reliable gain.

The owner’s requirement is to conserve Codex credits for real differentiation; see [CREDIT_OPTIMIZATION.md](CREDIT_OPTIMIZATION.md).
