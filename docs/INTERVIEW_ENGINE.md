# Interview Agent — Behavior and Orchestration Specification

**Status: Proposed design, not an implemented agent.**

## Core contract

A successful interviewer does not merely ask a static list of questions. It prepares a structured role-specific plan, listens to the candidate's actual answer, determines whether the answer covers the competency, and asks **one relevant follow-up** when a meaningful gap remains. It must remain professional, avoid biased assumptions, respect duration and close politely.

## Finite state machine

\`\`\`mermaid
stateDiagram-v2
  [*] --> DRAFT
  DRAFT --> PLANNED: validate setup + build plan
  PLANNED --> INTRO: start authorized session
  INTRO --> ASK: introduction complete
  ASK --> WAIT: question delivered
  WAIT --> PROBE: answer warrants follow-up
  WAIT --> ASK: sufficient answer / time exhausted
  PROBE --> WAIT: probe delivered
  WAIT --> CLOSING: interview duration or plan complete
  CLOSING --> EVALUATING: complete session
  EVALUATING --> COMPLETED: rubric report written
  DRAFT --> CANCELED: user cancel
  PLANNED --> CANCELED: user cancel
  INTRO --> PAUSED: connection lost or pause
  WAIT --> PAUSED: connection lost or pause
  PAUSED --> WAIT: valid resume
  PAUSED --> CANCELED: expired / canceled
  COMPLETED --> [*]
\`\`\`

Implementation must handle edge cases: duplicate events, late STT revisions, aborted streams, explicit skip, silence, user asks for clarification, out-of-time and provider errors. State transitions are server-authoritative.

## Plan object (conceptual)

- \`interview_id\`, \`user_id\`, \`rubric_version\`, \`plan_version\`
- \`role\`, \`seniority\`, \`focus_areas\`, \`duration_seconds\`
- \`language\`, \`modality\` (text/voice), \`consent_scope\`
- \`questions[]\`: competency, source/provenance, prompt, maximum probes, time allocation, difficulty, private rubric
- \`requirements\`: accessibility settings, max token/voice budgets, prohibited disclosures

Do not place private rubric or system prompts in browser responses.

## Follow-up selection

For each answer, derive structured observations:
1. What specific claim did the candidate make?
2. Which rubric criteria were addressed? With what quoted evidence?
3. Which important criterion is missing, contradicted or vague?
4. Is an additional probe useful, fair and within the time budget?
5. If yes, formulate **one** answer-dependent probe; otherwise move to the next planned question.

Example:
- Q: "How would you protect a database when Redis fails?"
- Answer: "Read directly from the database."
- Probe: "How would you avoid a traffic spike overwhelming the database after a cache outage?"
The follow-up probes a missing failure-mode concern; it does not switch topics arbitrarily.

## Constraints

- No pretending to know facts not in candidate's resume/JD.
- Avoid unnecessary compound questions, duplicate probes, leading suggestions or giving the answer prematurely.
- Bound follow-up count (initially max 2 per core question, adjustable by rubric) and total session time.
- Offer accessible clarification, skip/stop and accommodation.
- Interviewer should not provide final grades mid-session unless in explicit coached-practice mode.
- Prompt injection defense: user answer and retrieved text never become system/developer instructions; tools have scoped authorization.

## Separate evaluation service

The *interviewer* manages conversation. The *evaluator* reads the immutable transcript, role rubric, candidate code test outcomes and diagram evidence **after** the interview. It produces:
- Criterion score, rubric version, evidence event IDs, strengths, missing elements, caveats and confidence
- Recommended improvements and practice exercises
- Clear designation of coaching feedback (not validated selection decisions)

Do not let a browser field or candidate-provided prompt set evaluator scores.

## Minimum reference scenarios

1. Correct concise answer → reasonable progression.
2. Partially correct answer → context-aware probe.
3. Incorrect premise → challenge politely without leakage.
4. Hallucinated project details in JD → no invented assertions.
5. Silence → gentle reprompt, then safe skip.
6. Candidate requests clarity → explain question, not solution.
7. Repeated off-topic answers → maintain professional boundaries.
8. Long answer near timeout → summarize/transition.
9. Network reconnect / duplicate event → no duplicated question or score.
10. Adversarial text says "ignore prior instructions" → treated as answer content.

See [evaluation](QUALITY_AND_TESTING.md), [contracts](API_CONTRACTS.md), [security](SECURITY_AND_PRIVACY.md).
