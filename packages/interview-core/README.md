# Framework-independent Interview Core — Initial Implementation

This is the **first actual executable code** in the AI Interview repository. It is a small, dependency-free Node.js state machine and test suite created while the Euron runtime audit is pending. It does **not** duplicate the Euron web app, authentication, database, real-time voice, provider integration or AI planning.

## Run locally

Requires Node.js >=22; no npm install required:

    node --test packages/interview-core/test/*.test.mjs

From this directory:

    npm test

## Implemented

- Validated, bounded question plans with competencies and follow-up caps
- Owner-scoped interview session transitions and server-authoritative timeline
- Answer-dependent follow-up decision interface, supplied by a **trusted server-side policy** (not by the candidate)
- Idempotent submitted answers, skip, early finish, end-on-plan completion and duration expiration
- Immutable snapshot updates (the caller must persist with a DB transaction and optimistic lock)
- Practice report builder requiring real candidate-answer event references
- A stricter `compileEvidenceReport` contract that checks rubric membership, exact candidate quotations, question-to-criterion mappings, and evidence references for each observation; permits `null` scores when evidence is insufficient
- Adversarial and edge-case unit tests without paid LLM calls

## Not implemented — important

- **No LLM or adaptive AI**. The server must later generate and validate a \`{kind:"probe",text:"..."}\` or \`{kind:"next"}\` decision.
- **No HTTP authentication or database**. \`actorId\` is assumed to have been verified by a secure upstream layer, and snapshots are in memory.
- **No persistent idempotency or distributed concurrency safety**. Production implementation needs transactions and version checks.
- **No real hiring or psychometric scoring**; grades are supplied by a trusted evaluator and must be calibrated separately.
- **No guarantee a score or observation is correct**. A real quotation proves only that the cited text occurs in an allowed answer; a model can still misinterpret it. `compileEvidenceReport` validates a trusted evaluator's output and does not call an evaluator itself. The older `compilePracticeReport` validates event IDs only; use the stricter contract for new work.
- **No frontend, resume parser, voice, coding sandbox, whiteboard or deployment**.

## Integration guidance

Before merging this domain policy into Euron, audit its existing interview/service implementation. If Euron already meets the same requirements, prefer adapting/extending Euron rather than maintaining competing state machines. The goal here is to exercise and test the intended behavior under a narrow contract, not mandate a new runtime service.

Read [Interview Engine](../../docs/INTERVIEW_ENGINE.md) and [Implementation Checklist](../../docs/IMPLEMENTATION_CHECKLIST.md).

## Evidence report contract

After authenticating the owner and loading the authoritative completed session, the server selects a trusted rubric. It must never accept the rubric, scores or evaluator identity from the candidate's browser. A rubric criterion names the questions that may support it:

```js
import { compileEvidenceReport } from "./index.mjs";

const report = compileEvidenceReport(completedSession, {
  actorId: authenticatedUserId,
  rubricVersion: "backend-v1",
  rubric: [{ id: "resilience", label: "Failure handling", questionIds: ["cache"] }],
  assessments: [{
    criterionId: "resilience",
    score: 3, // 0–5, or null when there is insufficient evidence
    confidence: "low", // low, medium, high; use "insufficient" with a null score
    evidence: [{ eventId: "session-1:2", quote: "rate-limit requests" }],
    observations: [{ kind: "strength", text: "Considered load.", evidenceIndexes: [0] }],
  }],
});
```

Evidence indexes are zero-based and refer to the same criterion's `evidence` array. A scored criterion needs at least one exact quotation and one linked observation; each observation must cite evidence. If a question was skipped, use `score: null`, `confidence: "insufficient"`, and empty evidence/observations instead of inventing a grade. The contract rejects missing or duplicate rubric criteria, evidence from another question or interviewer, fabricated quotes and unknown assessment fields. The server should discard malformed evaluator output and present a retry or an unscored result; it should not silently replace it with a high score.

This module is not wired to an HTTP endpoint, database, application UI, or AI model. That integration is a later task after the foundation and its server-authored transcript model are selected.
