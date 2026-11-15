# Feature Inventory and Reuse Matrix

> **CRITICAL STATUS:** This repository contains documentation and a dependency-free **interview-core policy prototype**, not the end-user application. All product capabilities below remain **planned**, regardless of what an upstream README claims. Review this table after importing or implementing real code.

Legend: P0 = first working interview; P1 = competitive candidate product; P2 = commercial/enterprise. Source statuses are **upstream claims pending audit**. Change this table only after tests/inspection.

| Capability | Priority | Proposed source / implementation | Current project status | Acceptance evidence |
| --- | --- | --- | --- | --- |
| Login, account, roles | P0 | Audit Euron auth, retain if secure | Not implemented | Auth + cross-user tests |
| Candidate UI/dashboard | P0 | Audit Euron Next.js; redesign only as needed | Not implemented | Responsive E2E walkthrough |
| Resume/JD ingestion | P0 | Audit Euron parser and plan generation | Not implemented | File safety and parsing tests |
| Interview plan | P0 | Euron or DeepInterview concepts | Not implemented | Typed schema + fixtures |
| Adaptive questioning | P0 | Own state machine; review DeepInterview | Not implemented | Follow-up scenario suite |
| Text interview and transcript | P0 | Own API and event persistence | Not implemented | End-to-end saved interview |
| Evidence-backed evaluator | P0 | Own rubric service and structured output | Partial prototype: evidence contract only; no evaluator service or app integration | Expert-reviewed scoring samples and integration |
| Voice STT / TTS | P1 | LiveKit + configurable speech adapters | Not implemented | Real device + reconnection tests |
| Streaming speech interruption | P1 | LiveKit Agents | Not implemented | Barge-in latency test |
| Coding editor | P1 | Existing Euron editor or Monaco | Not implemented | Editor + autosave E2E |
| Secure code execution | P1 | Piston self-hosted, sandbox hardened | Not implemented | Adversarial execution tests |
| System design board | P1 | Excalidraw package | Not implemented | Persist/reopen diagram |
| Synchronized replay | P1 | New event timeline | Not implemented | Timestamp correctness |
| Coaching/progress | P1 | Own goal/rubric-linked experience | Not implemented | Repeat-session comparison |
| Evaluation regression | P0 | Promptfoo + curated golden set | Not implemented | CI thresholds |
| AI observability | P0 | OpenTelemetry; Langfuse if fit | Not implemented | Redacted trace demo |
| Model serving | P1 | Hosted adapter initially; vLLM when justified | Not implemented | Provider contract suite |
| Fine-tuning | P1 | Qwen-family + Unsloth/TRL QLoRA | Not implemented | Held-out measured gain |
| Admin, quotas, reports | P1 | Audit Euron first | Not implemented | RBAC and metering tests |
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
