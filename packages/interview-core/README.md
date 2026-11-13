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
- Adversarial and edge-case unit tests without paid LLM calls

## Not implemented — important

- **No LLM or adaptive AI**. The server must later generate and validate a \`{kind:"probe",text:"..."}\` or \`{kind:"next"}\` decision.
- **No HTTP authentication or database**. \`actorId\` is assumed to have been verified by a secure upstream layer, and snapshots are in memory.
- **No persistent idempotency or distributed concurrency safety**. Production implementation needs transactions and version checks.
- **No real hiring or psychometric scoring**; grades are supplied by a trusted evaluator and must be calibrated separately.
- **No frontend, resume parser, voice, coding sandbox, whiteboard or deployment**.

## Integration guidance

Before merging this domain policy into Euron, audit its existing interview/service implementation. If Euron already meets the same requirements, prefer adapting/extending Euron rather than maintaining competing state machines. The goal here is to exercise and test the intended behavior under a narrow contract, not mandate a new runtime service.

Read [Interview Engine](../../docs/INTERVIEW_ENGINE.md) and [Implementation Checklist](../../docs/IMPLEMENTATION_CHECKLIST.md).
