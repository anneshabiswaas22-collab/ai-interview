# Feature Inventory and Reuse Matrix

> **DEVELOPMENT STATUS:** An adapted candidate application is now present under `foundation/euron`. Its imported features are development-preview capabilities, not production-ready claims. The default demo uses deterministic stand-ins; verify the actual imported copy and real providers separately.

Legend: P0 = first working interview; P1 = competitive candidate product; P2 = commercial/enterprise. Source statuses are **upstream claims pending audit**. Change this table only after tests/inspection.

| Capability | Priority | Proposed source / implementation | Current project status | Acceptance evidence |
| --- | --- | --- | --- | --- |
| Login, account, roles | P0 | Euron auth | Imported for development; security review pending | Auth + cross-user tests |
| Candidate UI/dashboard | P0 | Euron Next.js | Imported for development | Responsive E2E walkthrough |
| Resume/JD ingestion | P0 | Euron parser and plan generation | Imported; privacy review pending | File safety and parsing tests |
| Interview plan | P0 | Euron planning | Imported; default model is a stub | Typed schema + fixtures |
| Adaptive questioning | P0 | Provider-backed interview | Adapters imported; real-provider validation pending | Follow-up scenario suite |
| Text interview and transcript | P0 | Euron API and persistence | Consent-based text mode added for development, with server-selected questions, durable history and retry handling; voice transcript remains client-authored | End-to-end saved interview |
| Evidence-backed evaluator | P0 | Own rubric service and structured output | Not implemented | Expert-reviewed scoring samples |
| Voice STT / TTS | P1 | Configurable provider adapters | Imported; real audio not verified | Real device + reconnection tests |
| Streaming speech interruption | P1 | LiveKit Agents | Not implemented | Barge-in latency test |
| Coding editor | P1 | Existing Euron editor | Imported; no secure code execution | Editor + autosave E2E |
| Secure code execution | P1 | Piston self-hosted, sandbox hardened | Not implemented | Adversarial execution tests |
| System design board | P1 | Excalidraw package | Not implemented | Persist/reopen diagram |
| Synchronized replay | P1 | New event timeline | Not implemented | Timestamp correctness |
| Coaching/progress | P1 | Own goal/rubric-linked experience | Not implemented | Repeat-session comparison |
| Evaluation regression | P0 | Promptfoo + curated golden set | Not implemented | CI thresholds |
| AI observability | P0 | OpenTelemetry; Langfuse if fit | Not implemented | Redacted trace demo |
| Model serving | P1 | Hosted adapter initially; vLLM when justified | Not implemented | Provider contract suite |
| Fine-tuning | P1 | Qwen-family + Unsloth/TRL QLoRA | Not implemented | Held-out measured gain |
| Admin, quotas, reports | P1 | Euron | Imported for development; security and evidence review pending | RBAC and metering tests |
| Subscription/payment | P2 | Approved payment provider SDK | Not implemented | Webhook/idempotency tests |
| Recruiter/org accounts | P2 | New tenant/reviewer layer | Not implemented | Tenant isolation & access checks |
| Human-reviewed hiring assessments | P2 | New validated assessment system | Not implemented | Assessment validity/fairness study |

## Working policy prototype (not an application feature)

The [interview-core module](../packages/interview-core/README.md) supplies a bounded, owner-scoped interview state policy and evidence-linked coaching report input validation, with passing Node tests. It does **not** provide real adaptive AI, user authentication, persistence, voice or product reports. After the Euron source audit, reuse whichever session state model is sound and avoid maintaining redundant engines.

## Avoid duplicate effort

Do not simultaneously introduce Euron auth + Supabase auth, Euron editor + Monaco replacement, multiple job queues, multiple video transports or several evaluation frameworks. Pick one primary implementation per concern, behind an interface.

## Evidence checklist for changing status

When a row moves to "implemented", link:
1. Source commit/PR and affected paths.
2. Real execution steps in dev/prod-like environment.
3. Unit/integration/E2E test outputs.
4. Security/license impact.
5. Remaining caveats and real-provider limitations.

## Proposed review cycle

Audit matrix at each milestone and whenever upgrading an upstream dependency. Every missing feature must become an issue with bounded scope and acceptance criteria.
