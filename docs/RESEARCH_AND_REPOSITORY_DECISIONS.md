# AI Interview Platform — Research, Repository Decisions and Reference Links

Last consolidated: 2026-11-16

This file records the public repositories, model resources, architectural conclusions, license considerations and reuse decisions discussed during the project.

It is intentionally more research-focused than MASTER_PROJECT_HANDOFF.md.

## 1. Final application-level repository decision

Exactly two application-level repositories are primary:

1. Euron Open Conversation
2. DeepInterview

Everything else is a component candidate, optional technology, alternative implementation or research reference.

### Euron Open Conversation

Repository:
https://github.com/euron-sde-team/euron-open-real-time-ai-conversation-system

Verified revision:
216a8fc52a055587f436f2446f1a80b6868bd14a

License:
MIT

Decision:
Primary application foundation.

Reasoning:

- strongest direct stack compatibility with current product;
- already adapted into foundation/euron;
- real Next.js + Express + PostgreSQL + Redis structure;
- candidate dashboard and interview workflows already exist;
- auth and admin infrastructure already exist;
- provider-neutral model abstractions exist;
- report/history/export structures exist;
- realtime provider structure exists;
- lowest integration cost because replacing it now would throw away working code.

Risk:
Very shallow upstream history at the studied revision. Our fork must be owned and maintained as our product.

### DeepInterview

Repository:
https://github.com/ngoanpv/DeepInterview

Verified revision:
bd6d136fffc509265bc2355e95101e0ad7f56eac

License:
Apache-2.0

Decision:
Primary interview-intelligence and architecture reference.

Studied source:

- apps/agent/src/deepinterview_agent/prep/nodes.py
- apps/agent/src/deepinterview_agent/live/director.py
- apps/agent/src/deepinterview_agent/live/interviewer.py
- apps/agent/src/deepinterview_agent/post/evaluator.py
- apps/agent/src/deepinterview_agent/post/verifier.py
- apps/agent/tests/test_adaptive.py
- apps/agent/tests/test_score.py

Useful ideas:

- preparation/live/post separation;
- interview coverage planning;
- adaptive difficulty policy;
- answer-aware follow-ups;
- lifecycle limits;
- competency-level evaluation;
- per-question evaluation;
- post-evaluation verification;
- avoiding automatic failure for unanswered/skipped items.

Decision boundary:
Port ideas into the existing TypeScript application. Do not create a second Python backend.

## 2. Why other interview applications were not selected as main foundations

### GrillKit

Repository:
https://github.com/Forkfield/grillkit

License snapshot:
Apache-2.0.

Useful for:

- technical interview tracks;
- timing;
- coding exercises;
- grading concepts;
- local voice patterns.

Why not a main foundation:

- another application stack would duplicate existing product infrastructure;
- its coding workflow references Judge0, whose GPL-3.0 licensing is less attractive for the intended commercial product;
- current Euron-derived application already has more directly reusable platform infrastructure.

Status:
Research reference.

### Interview GPT

Repository:
https://github.com/daixinwang/interview-gpt

License snapshot:
MIT.

Observed architecture includes:

- apps/api Python backend;
- agent modules;
- evaluator/interviewer/reporter;
- Redis session state;
- Next.js frontend.

Useful for:

- small multi-agent patterns;
- interviewer personalities;
- follow-up ideas;
- report/evaluator separation.

Why not a main foundation:
Would add a second Python backend and duplicate functionality already implemented.

Status:
Research reference.

### Interviewa

Repository:
https://github.com/sh78ba/Interviewa

License snapshot:
AGPL-3.0-or-later.

Useful for:

- resume-aware technical interviewing;
- voice;
- reporting;
- provider experiments.

Why not a main foundation:
AGPL network-use obligations are a material commercial consideration, and another Python application would duplicate the current stack.

Status:
Research only unless license obligations are intentionally accepted.

### Local AI Interviewer

Repository:
https://github.com/Yuvakunaal/local-ai-interviewer

License snapshot:
MIT.

Useful for:

- privacy-oriented local mode;
- Ollama integration;
- local STT/TTS;
- offline evaluation;
- candidate profile and adaptive ideas.

Why not a main foundation:
Large alternative Python backend would duplicate authentication/session/database responsibilities.

Status:
Useful privacy/local-mode reference.

## 3. Voice and speech references

### LiveKit Agents

https://github.com/livekit/agents

License:
Apache-2.0.

Potential use:

- low-latency turn-taking;
- voice transport;
- agent tooling;
- interruption handling.

Decision:
Only integrate if it materially improves the existing realtime architecture. Do not add it merely because it is popular.

### faster-whisper

https://github.com/SYSTRAN/faster-whisper

License:
MIT for source.

Potential use:
Optional self-hosted STT provider.

Important:
Exact model weights have separate terms and must be reviewed independently.

### Kokoro 82M

https://huggingface.co/hexgrad/Kokoro-82M

Potential use:
Low-cost local/self-hosted TTS experiments.

Important:
Verify checkpoint and voice-asset licensing before bundling or commercial use.

## 4. Open LLM training and inference references

### Unsloth

https://github.com/unslothai/unsloth

License snapshot:
Apache-2.0 core; verify optional components.

Potential use:
QLoRA/SFT experiments after baseline quality exists.

### Unsloth notebooks

https://github.com/unslothai/notebooks

License snapshot at research time:
LGPL-3.0.

Potential use:
Reference recipes for external Colab/GPU experimentation.

Decision:
Do not copy blindly; verify exact notebook terms.

### PEFT

https://github.com/huggingface/peft

License:
Apache-2.0.

Potential use:
LoRA/adapter training dependency.

### TRL

https://github.com/huggingface/trl

License:
Apache-2.0.

Potential use:
SFT/preference optimization.

### vLLM

https://github.com/vllm-project/vllm

License:
Apache-2.0.

Potential use:
Scalable self-hosted GPU inference later.

Decision:
Do not add until real economics and latency justify GPU hosting.

### Ollama

https://github.com/ollama/ollama

License:
MIT.

Potential use:
Local developer/self-hosted provider.

### llama.cpp

https://github.com/ggml-org/llama.cpp

License:
MIT.

Potential use:
Quantized CPU/GPU local inference.

Decision:
Alternative to other self-hosting approaches. Avoid maintaining multiple overlapping serving stacks without evidence.

### Qwen3-4B

https://huggingface.co/Qwen/Qwen3-4B

Role:
Potential first open-weight benchmark/fine-tuning candidate.

Requirement:
Verify exact checkpoint license and derivative/commercial terms at training time.

### Qwen3.5-9B

https://huggingface.co/Qwen/Qwen3.5-9B

Role:
Potential larger benchmark candidate.

Requirement:
Verify current availability, license, memory cost and benchmark benefit before adoption.

## 5. Coding interview references

### Piston

https://github.com/engineer-man/piston

License:
MIT.

Decision:
Preferred future code execution candidate, subject to a hostile-input security audit.

Required architecture:

- separate isolated service;
- strict CPU/memory/time/process limits;
- restricted filesystem;
- no normal production-network access;
- deterministic test input/output;
- immutable execution records for evaluation;
- never execute candidate code inside the Express API process.

### Monaco Editor

https://github.com/microsoft/monaco-editor

License:
MIT.

Decision:
Not needed now. The current application already has CodeMirror.

Only evaluate Monaco if a concrete editor limitation appears.

### Judge0

https://github.com/judge0/judge0

License:
GPL-3.0.

Decision:
Not preferred as default for this commercial product without legal review.

## 6. System-design whiteboards

### Excalidraw

https://github.com/excalidraw/excalidraw

License:
MIT.

Decision:
Preferred future whiteboard candidate.

Reuse:
Canvas/drawing package.

Build ourselves:

- interview-specific persistence;
- replay/versioning;
- candidate/session ownership;
- evidence connection;
- accessibility;
- evaluation logic.

### tldraw

https://github.com/tldraw/tldraw

License:
Repository-specific production licensing.

Decision:
Optional comparison only. Do not assume it is a free MIT production alternative.

## 7. AI quality and observability

### Promptfoo

https://github.com/promptfoo/promptfoo

License:
MIT.

Potential use:

- evaluator regression tests;
- prompt comparisons;
- red-team cases;
- prompt-injection tests;
- CI quality gates.

Decision:
Strong candidate for the model/evaluator quality phase.

### Langfuse

https://github.com/langfuse/langfuse

License:
MIT core; some enterprise areas differ.

Potential use:

- traces;
- token/cost analysis;
- prompt quality monitoring;
- evaluator debugging.

Important:
Never send raw candidate PII/resumes to an observability platform without privacy review/redaction.

## 8. Commercial infrastructure

### Stripe Node

https://github.com/stripe/stripe-node

License:
MIT.

Role:
Potential later subscription/billing integration.

Decision:
Not an immediate dependency. Validate business/payment availability and demand first.

## 9. Proprietary market benchmarks

These products are benchmarks only. Do not copy proprietary code, interview questions, recordings or brand assets.

### Hello Interview
https://www.hellointerview.com/

Benchmark:
Technical interview and system-design candidate experience.

### Final Round AI
https://www.finalroundai.com/

Benchmark:
Personalized preparation and candidate workflows.

### Huru
https://huru.ai/

Benchmark:
General interview practice and voice/video flow.

### Yoodli
https://yoodli.ai/

Benchmark:
Speaking and communication coaching.

### CodeSignal
https://codesignal.com/

Benchmark:
Technical assessment security and coding workflows.

### HireVue
https://www.hirevue.com/

Benchmark:
Employer-side governance and assessment operations.

## 10. Research decision matrix

| Candidate | Application compatibility | License fit | Integration complexity | Primary value | Final role |
|---|---|---|---|---|---|
| Euron | Excellent | Strong | Low because already integrated | Product foundation | PRIMARY #1 |
| DeepInterview | Good conceptually | Strong | Low if concepts are ported, high if app imported | Interview intelligence | PRIMARY #2 |
| GrillKit | Moderate | Strong | High as app | Technical/coding patterns | Reference |
| Interview GPT | Moderate | Strong | High as second backend | Multi-agent patterns | Reference |
| Interviewa | Moderate | Weak for closed commercial integration due AGPL | High | Resume/voice ideas | Research |
| Local AI Interviewer | Moderate | Strong | High as second backend | Local/privacy mode | Reference |
| LiveKit Agents | Component | Strong | Medium | Voice transport | Optional component |
| Piston | Component | Strong | Medium/High security work | Deterministic code execution | Preferred future component |
| Excalidraw | Component | Strong | Medium | Whiteboard | Preferred future component |
| Promptfoo | Component/tooling | Strong | Low/Medium | Model quality regression | Preferred future tooling |

## 11. Reference architecture reuse chart

~~~mermaid
flowchart LR
    Product[Our Owned AI Interview Product]

    Euron[Euron]
    Deep[DeepInterview]
    LiveKit[LiveKit]
    Whisper[faster-whisper]
    Piston[Piston]
    Excalidraw[Excalidraw]
    Promptfoo[Promptfoo]
    Langfuse[Langfuse]
    Train[Unsloth / PEFT / TRL]
    Serve[vLLM / Ollama / llama.cpp]

    Euron -->|foundation code already adapted| Product
    Deep -->|ideas ported into TypeScript| Product
    LiveKit -. optional voice .-> Product
    Whisper -. optional STT .-> Product
    Piston -. future isolated execution .-> Product
    Excalidraw -. future whiteboard .-> Product
    Promptfoo -. future eval CI .-> Product
    Langfuse -. optional redacted tracing .-> Product
    Train -. only after baseline .-> Product
    Serve -. only if economics justify .-> Product
~~~

## 12. Why not merge multiple application repositories

Combining entire applications creates:

- duplicate authentication systems;
- conflicting databases;
- multiple session models;
- incompatible state transitions;
- more secrets/providers;
- more dependency vulnerabilities;
- harder migrations;
- duplicated UI;
- harder debugging;
- higher hosting cost;
- unclear ownership of business logic.

Therefore:

- reuse components through adapters;
- port algorithms;
- preserve one authoritative application.

## 13. License/NOTICE reminders

Before copying source from any repository:

1. pin the exact revision;
2. read LICENSE;
3. read NOTICE if present;
4. inspect third-party assets;
5. inspect generated/vendor content;
6. inspect model/checkpoint licenses separately;
7. record attribution in the project's third-party notice;
8. confirm commercial compatibility;
9. do not assume GitHub metadata is legally complete.

Specific reminders:

- DeepInterview Apache-2.0 has NOTICE obligations when copying source.
- Judge0 GPL-3.0 is not the preferred default.
- Interviewa AGPL has network-use source obligations.
- tldraw production licensing requires review.
- model weights can have different terms from their code repository.

## 14. Recommended technology progression

~~~mermaid
flowchart TD
    Foundation[Existing Euron Foundation]
    Trust[Trustworthy Written Evaluation]
    Benchmark[Expert Quality Benchmark]
    Adaptive[Adaptive Text Interviewing]
    Voice[Authoritative Voice]
    Code[Secure Code Execution]
    Board[System Design Whiteboard]
    Observe[Quality / Cost Observability]
    Train[Optional Fine-tuning]
    Serve[Optional Self-hosted Serving]
    Beta[Candidate Beta]

    Foundation --> Trust
    Trust --> Benchmark
    Benchmark --> Adaptive
    Adaptive --> Voice
    Adaptive --> Code
    Adaptive --> Board
    Benchmark --> Observe
    Observe --> Train
    Train --> Serve
    Voice --> Beta
    Code --> Beta
    Board --> Beta
~~~

The ordering is deliberate.

Do not move model training ahead of benchmark quality.

Do not move code execution ahead of isolation/security design.

Do not move employer decision workflows ahead of candidate-practice validation.

## 15. Repository links that future developers should keep open

Project:
https://github.com/anneshabiswaas22-collab/ai-interview

Current evidence-feedback PR at consolidation:
https://github.com/anneshabiswaas22-collab/ai-interview/pull/22

Primary upstream foundation:
https://github.com/euron-sde-team/euron-open-real-time-ai-conversation-system

Primary intelligence reference:
https://github.com/ngoanpv/DeepInterview

Full maintained source list:
REFERENCE_REPOSITORIES.txt

Master project memory:
docs/MASTER_PROJECT_HANDOFF.md

Fresh-chat continuation prompt:
docs/AI_CONTINUATION_PROMPT.md

## 16. Final research conclusion

The best path is not to search for a magical third repository.

The highest-value strategy is:

- own and harden the current Euron-derived application;
- port DeepInterview's strongest adaptive/evaluation ideas;
- use focused components such as Piston and Excalidraw only when their phase arrives;
- measure evaluator quality before training;
- keep provider and infrastructure choices replaceable;
- prioritize trustworthy candidate coaching over feature count.
