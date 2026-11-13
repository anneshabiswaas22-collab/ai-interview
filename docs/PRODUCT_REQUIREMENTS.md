# Product Requirements (PRD)

**Status:** Proposed, no implementation in this repository as of 2026-11-13. Priorities: P0 essential, P1 competitive depth, P2 expansion. "Done" requires real integration and tests, not mocks.

## Personas and user stories

| Persona | Need | Acceptance signal |
| --- | --- | --- |
| Junior engineer | Practice an accessible technical interview | Questions match chosen level; feedback explains errors |
| Mid/senior engineer | Deep, realistic follow-ups and system design | AI probes design choices, scaling and failure scenarios |
| Resume-led candidate | Prepare for questions on actual projects | AI refers only to authorized resume/JD facts |
| Candidate needing speaking practice | Rehearse answers aloud | Stable captions, interruption handling and replay |
| Admin | Run secure, affordable application | Quotas, cost visibility, RBAC and audit trail |
| Recruiter (later) | Assess role-relevant skills fairly | Validated rubric, human review and appeals process |

## P0 — product loop

**F-001 Authentication & profile**
- Sign up/sign in/out, session revocation, profile settings, roles and tenant boundaries.
- Reuse existing implementation if vetted; avoid starting a second auth system.
- Acceptance: unauthorized endpoints reject users; cross-user access tests pass.

**F-002 Interview setup**
- Role, seniority, focus topics, format, time budget and consent.
- Optional resume/JD: validate file size/type; parse and minimize retention; display what was extracted.
- Acceptance: invalid inputs rejected; profile/JD details are never fabricated.

**F-003 Interview plan**
- Generate structured topics, difficulty, target competencies, question pool and time allocations.
- No ability to change server-side policy by submitting candidate instructions.
- Acceptance: JSON schema validates; plan is bounded by time/rubric; reproducible fixtures.

**F-004 Adaptive interview**
- State machine (INTRO → QUESTION → LISTEN → PROBE/TRANSITION → CLOSING → COMPLETE).
- Track prior answers, max probes, time remaining, repeated questions and interruptions.
- Acceptance: 10+ scenario tests including incorrect, incomplete, silent, off-topic and excellent answers.

**F-005 Transcript and resumable session**
- Server-authored transcript events with timestamps and speaker; safe resume after reconnect.
- Acceptance: ordering and idempotency preserved; unauthorized session reads denied.

**F-006 Evidence-backed feedback**
- Separate interviewer from evaluator; rubric and evidence spans; strengths, gaps, uncertainty, actionable drills.
- Acceptance: every material assertion references a transcript segment or deterministic test outcome.

**F-007 Dashboard**
- View completed interviews, filters, role trends, recent feedback; deletion and data export.
- Acceptance: responsive and keyboard-accessible; no cross-user data.

## P1 — differentiating capabilities

**F-008 Realtime voice:** WebRTC/LiveKit where justified; STT, model, TTS provider adapters; barge-in, reconnect, captions, costs, latency metrics.

**F-009 Coding interview:** editor, public/hidden tests, server-owned grading, isolated execution, limits and audit logs.

**F-010 System-design board:** Excalidraw integration; diagram persistence, verbal explanation, rubric-based critique of tradeoffs; do not treat visual style as skill score.

**F-011 Replay:** synchronized transcript, optional authorized audio, diagrams, code snapshots and feedback markers.

**F-012 Personalized coaching:** study plan, practice recommendations and progress metrics with rubric versioning.

**F-013 Multi-model:** provider adapter for hosted and local endpoints; routing, fallbacks, prompt versions, evaluation and inference costs.

**F-014 Finetuning:** reviewed original data, adapter training, benchmark comparison, model registry, canary and rollback.

## P2 — commercial/enterprise

**F-015 Billing:** provider integration, usage metering, subscriptions, payment-status reconciliation, refunds and entitlements.

**F-016 Organizations:** secure tenant separation, recruiters, candidate invitations, configurable interviews, reviewer audit trail.

**F-017 Integrations:** documented API/webhooks, optional ATS connections, rate limits, retry semantics.

**F-018 Governance:** accommodations, validated scoring, human review, dispute/appeal path and jurisdiction-specific compliance.

## Shared nonfunctional requirements

- Security: secrets never in Git; RBAC and tenant tests; adversarial prompt-injection test suite; rate limits.
- Privacy: consent before audio capture and PII processing, encryption, retention and deletion controls.
- Quality: deterministic unit tests and human-graded interview samples; no invented LLM accuracy.
- Operations: health checks, tracing with PII redaction, per-session costs, graceful fallbacks.
- Accessibility: WCAG 2.2 AA aim, keyboard-only workflows, captions, text alternative to voice.
- Scale: start small, profile and load-test before committing to GPU/infra spend.

## First vertical slice (minimum useful implementation)

One authenticated candidate creates a text interview for backend SDE II, answers 5–8 questions with one or two adaptive probes, ends the session, and receives transcript-backed feedback saved in history. Use a replaceable model adapter and real database persistence. This is the first end-to-end acceptance test.

## Explicit exclusions for first beta

Facial-analysis scores, secretive live-interview copilot, automated hire/reject decisions, celebrity voices/avatars, complex billing plans, video proctoring by default, guaranteed interview outcomes, copied premium question banks.

References: [interview engine](INTERVIEW_ENGINE.md), [API proposal](API_CONTRACTS.md), [security](SECURITY_AND_PRIVACY.md).
