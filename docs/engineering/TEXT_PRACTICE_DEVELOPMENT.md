# Text practice: development slice

This slice adds written mock interviews to the existing development candidate. It reuses its accounts, stored interview plan, PostgreSQL database, scoring worker and reports. A consent checkbox is required before the first question; the candidate's answers are saved and may be sent to the configured text model. No audio, camera or code execution is involved. Starting text practice disables the interview-specific proctoring flag, including when it was selected during planning. A code question is answered as a written explanation.

## Contract and security

- `POST /api/interviews/{id}/text/start` takes exactly `{ "consent": true }`. It starts only a ready, owned interview and records when consent was given. Repeating it returns the existing session.
- `GET /api/interviews/{id}/text` returns the owner's ordered history. Other users receive 404.
- `POST /api/interviews/{id}/text/answers` takes `{ requestId, expectedVersion, text }`. The request ID is a UUID; text is non-empty and at most 8,000 characters. The server chooses the question and position from the frozen plan. Extra fields, including client-authored questions, are rejected.
- A transaction locks the interview row and updates history, position and idempotency records together. A retry using the same request and contents returns current state, including after completion; reusing its ID with different contents or answering an old version returns 409. Each question can be answered once.
- Text and voice modes are mutually exclusive. The older generic answer API rejects text sessions. Questions and answers are included in the account export and cascade-delete with their interview.

## Scope and acceptance

Check the feature PR's clean database and offline browser workflow. Its integration suite checks owner isolation, consent, untrusted extra fields, replay, concurrent answers, mode isolation, export and deletion. Its browser test covers consent, submit, reload and report. These tests use a simulated model, not a real provider.

Written scoring uses the existing worker and provider adapters with a strict `text-practice-v1` contract. Domain and written-communication assessments require exact quotations from persisted answer events for that question; each observation cites its criterion's evidence. Unknown fields, foreign events and invented quotations fail closed. Insufficient evidence remains unscored (`null`), not a fabricated floor score. The report displays quotations and evaluator-reported confidence; quotation validation does not prove semantic accuracy or calibrate confidence. Whole grounded feedback is withheld from public shares without transcript consent because observations can repeat private answer text. No new database migration or second interview engine is introduced. These guarantees are tested with synthetic providers; real-provider quality remains unvalidated. A transactional outbox records score dispatch with each answer and retries queue delivery after temporary failures. Queue acceptance is not proof of scoring; failed models, Redis durability, worker operations and other job types still need review. Voice transcript handling is separate and remains browser-authored. Adaptive follow-ups, safe code execution, real-provider verification, and security/accessibility review are not included here. Use synthetic test data.

## Rollback

Feature code and UI can be rolled back with a normal revert. The forward-only database migration adds tables and an enum value; do not edit or remove the applied migration in a deployed database. Preserve data and add a separately reviewed forward migration if database cleanup is required.
