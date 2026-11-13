# Quality, Testing and AI Evaluation Plan

**Status:** Tests are specified, not yet run for this project. The upstream applications' reported test counts are not this project's test results.

## Test pyramid

| Layer | What to test | Release gate |
| --- | --- | --- |
| Unit | state transitions, rubric calculations, schema validation, budgets, prompt boundaries | Required per changed component |
| Contract | versioned API/event schemas, provider adapter and model output schemas | CI green, no silent breaking changes |
| Integration | auth → planner → interview → report, DB, queue, adapters, idempotency | Recorded real outputs |
| E2E | browser setup → actual text interview → follow-ups → report/history | First P0 release gate |
| Real voice | microphone/device, STT/TTS, barge-in, high latency, dropped connection | Required before claiming voice is working |
| Coding security | hostile submissions, timeouts, egress probes, resource abuse, output overflow | Independent security approval |
| Accessibility | keyboard navigation, captions, screen readers, motion and text alternatives | Before public beta |
| Load/cost | p50/p95 response, provider concurrency, sessions/min, total session cost | Baseline and thresholds |
| AI regression | held-out follow-up/rubric cases, attack prompts, synthetic and expert review | Required before model/prompt update |

## Golden interview scenarios

Create versioned original fixtures. Include:
- Great, adequate, vague, incorrect, unrelated and adversarial answers.
- Follow-up that depends on candidate's last sentence; avoid repetitive generic probes.
- Insufficient time, skip, silence, pause/reconnect, transcript revision, empty resume and contradictory JD.
- Backend, frontend, SQL, coding, architecture, behavioral and resume-based topic coverage.
- Fairness/accessibility cases: non-native English, speech disfluencies, alternative response format.
- Injection attempts in resume, JD, code comments, retrieved documents and answer text.

## Human evaluation rubric (example 1–5)

Evaluate interviewer's output, not applicant's suitability:
1. **Relevance** — logically connected to the answer and assigned competency.
2. **Technical validity** — correct premise, not inventing facts or impossible constraints.
3. **Conversation control** — natural timing, one focused probe, responsive to uncertainty.
4. **Policy compliance** — respectful, no bias/inappropriate scoring, honors scope/time.
5. **Actionable feedback** — evidence-linked, clear and useful coaching.

Reviewers should see anonymized examples blinded to model variant. Record sample size, scoring rubric, inter-rater agreement and disagreement adjudication. Do not use one AI model alone as definitive evaluation of itself.

## Candidate-feedback evaluation

- Every graded criterion must cite one or more transcript events or deterministic code results.
- Explicitly mark insufficient evidence, rubric uncertainty and untested assumptions.
- Evaluate whether recommended drills address actual gaps.
- Never infer personality, emotion, ethnicity, disability, attractiveness or accent quality as competency.

## AI safety and prompt injection

- Candidate text cannot override system instructions, scoring source of truth, tools or auth.
- Resume/JD/document content labeled untrusted, isolated in prompts and stripped of arbitrary tool directives.
- Promptfoo (or equivalent) CI cases target leakage, instruction hierarchy attacks and rubric tampering.
- Red-team unrestricted tool calls and sandbox escape attempts.
- Output schemas validated; incomplete or invalid scoring rejected/retried within bounded limits.

## Required experiment artifacts

- Dataset manifest with permission, source and version.
- Golden fixtures with split strategy; ensure no train/test contamination.
- Raw metric summaries with denominators, confidence intervals where appropriate.
- Provider/model/prompt/rubric versions, temperature/seed where supported and costs.
- Human reviewer instructions and anonymized evaluation reports.
- Regression comparison against last approved version.
- Model card and rollback instructions.

## First text-interview acceptance demonstration

1. Create account and start backend mid-level practice.
2. Receive a genuine plan grounded in selected role.
3. Answer 5–8 questions; agent asks useful contextual probes on at least two incomplete answers.
4. Stop; transcript and rubric-backed report persisted.
5. Reopen report from history as owner.
6. Unauthenticated/cross-user access denied and tested.
7. No PII leaked into logs and no browser-controlled grading.

**No part of this should be called "passed" until the test actually ran.**

## Automation strategy

Use deterministic tests on every PR, a small sampled Promptfoo suite for prompt changes, nightly broader AI comparisons when affordable, and periodic expert reviews. Fail open? No: safety and authorization are **fail-closed**. Speech provider outage may degrade to transparent text-only mode.

See [interview engine](INTERVIEW_ENGINE.md), [fine-tuning](MODEL_AND_FINETUNING.md), [security](SECURITY_AND_PRIVACY.md).
