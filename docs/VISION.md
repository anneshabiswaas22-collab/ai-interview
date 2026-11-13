# Product Vision, Users and Success Measures

_Last reviewed: 2026-11-13. This is a proposed product vision, not proof of achieved market position._

## North star

Build an **original, commercially viable AI Interviewer platform** that offers the depth of great human interviewers: preparation based on a candidate's experience, relevant follow-up questions, realistic spoken conversations, job-relevant evaluation, and useful coaching. Make it self-hostable, observable, and economical to operate. Use Codex/Astra plus proven public software instead of recreating commoditized components.

No one vendor has been proven universally "#1" across candidate preparation, coding tests, speaking coaching, and employer hiring. Our goal is to **compete against the strongest capabilities from each category**, not clone a proprietary product.

## Two audiences, different risk profiles

### 1. Candidate preparation (P0 — launch first)
- Software engineers: junior, mid-level, senior; backend, frontend, full-stack, AI/ML.
- Early interview types: behavioral/HR, resume/project deep dives, technical discussion, live coding, system design.
- Later: role/industry packs, English communication coaching, accessibility and language settings.
- User can see what the interviewer heard, pause/resume (when safe), revisit answers, and get constructive practice feedback.

### 2. Employers and recruiters (P2 — later gated track)
- Job-related interview templates, invite candidates, assess submissions, reviewer workflow, access controls and audit trails.
- **Not a fully automated hiring decision-maker.** Scores need validated rubrics, fairness/accessibility review and accountable human decisions.
- Deliberately separate practice "coaching scores" from consequential hiring recommendations.

## Core differentiators

1. **Grounded questioning:** Each question and follow-up ties to the role rubric, prior answer and candidate-authorized resume/job description.
2. **High-quality technical depth:** Test runnable code, examine tradeoffs, and reason about diagrams—not just produce a plausible score.
3. **Evidence-based coaching:** Every claim about candidate performance points to an answer, a test outcome or a rubric item; uncertainty is explicit.
4. **Low-latency, natural voice:** Responsive turn detection, transcripts, interruption handling, recoverable sessions.
5. **Model ownership/flexibility:** Open-weight model option, replaceable providers, reproducible training/evaluation; avoid single-vendor lock-in.
6. **Privacy-first defaults:** No unconsented recordings; consent, retention controls, deletion and restricted access.
7. **Credit efficiency:** Keep existing working auth/UI/report systems, integrate proven open-source packages, measure before rewriting.

## Candidate journey

1. Create account; select role, seniority, interview type, language, duration.
2. Optional: upload resume and paste JD, with explicit data handling notice.
3. System generates a personalized plan and candidate-visible topic outline (not answer keys).
4. AI introduces itself, conducts timed text/voice interview, listens, probes weaknesses and records transcript.
5. For code: candidate writes, runs, debugs and submits in a restricted sandbox. For system design: candidate explains diagram + tradeoffs.
6. End interview; receive itemized, evidence-backed coaching, sample improved answers and targeted practice exercises.
7. Return to dashboard to measure progress with comparable rubrics and repeat weak topics.

## Principles and non-goals

- Build a **mock interview/practice product**; do not target covert assistance in live third-party interviews.
- No facial-emotion, accent, eye-contact or inferred-personality scoring. Do not use sensitive or proxy demographic traits as fitness measures.
- No fake features, invented model performance metrics, copied private question banks, or "fully self-hosted" claims when provider APIs are required.
- A fine-tuned model is optional until it demonstrably outperforms a well-prompted base model on held-out tasks.
- Accessibility and human oversight are requirements, not postponed marketing additions.

## Initial measurable targets (hypotheses, tune after baseline)

| Dimension | Initial experiment target | How to verify |
| --- | --- | --- |
| Correct follow-up relevance | >= 80% reviewer-agreed relevant probes | Blind human ratings on held-out conversations |
| Technical feedback correctness | >= 90% correct rubric assertions | Expert review, with coded-answer ground truth |
| Voice experience | p95 response latency measured and trended; start target < 2.5 s | Client/agent time spans; hardware-specific |
| Session robustness | >= 99% no unexpected loss in beta | Session analytics and crash/reconnect tests |
| Cost | Cost per completed interview tracked by modality/provider | Per-session accounting, not guesses |
| Candidate usefulness | Majority rate feedback useful in moderated beta | Structured user interviews |

These are aspirations, not claims. Define statistical confidence and sample sizes before launch.

## Monetization hypothesis

Free limited practice; optional paid practice packs, longer voice interviews, personalized learning analytics; later employer seats/usage plans. Validate demand and payment eligibility before implementing billing. Avoid charging for a lower-quality automated screening system.

## Primary success criterion

**A first-time user completes an actual mock interview and can explain precisely what to improve next.** The software must work reliably, not merely display polished screens.

See [requirements](PRODUCT_REQUIREMENTS.md), [feature matrix](FEATURE_MATRIX.md) and [roadmap](ROADMAP.md).
