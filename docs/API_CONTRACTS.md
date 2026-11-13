# Proposed API and Event Contracts (v1)

**Draft design, not currently deployed.** Align with the adopted foundation after Milestone 1 audit. Avoid duplicating upstream APIs without reason. Use OpenAPI + generated client schemas once implementation begins.

## Authentication, ownership and conventions

- Every candidate endpoint requires authenticated identity; never trust a client-supplied \`user_id\`.
- Use \`/api/v1\` prefix, UUID/ULID identifiers, ISO-8601 UTC timestamps, pagination and explicit schema versioning.
- Send \`Idempotency-Key\` on session creation, event append, end and billing-sensitive calls.
- Standard errors: \`{ "error": { "code": "VALIDATION_ERROR", "message": "...", "request_id": "..." } }\`.
- Typed status codes: 400 invalid, 401 unauthenticated, 403 unauthorized, 404 not found (without leaking existence), 409 state conflict, 429 quota, 503 provider unavailable.

## Candidate endpoints — proposed

| Method | Route | Function |
| --- | --- | --- |
| POST | /api/v1/interviews | Create draft with role, level, modality, consent and optional source metadata |
| GET | /api/v1/interviews | Own sessions list, paginated |
| GET | /api/v1/interviews/:id | Session metadata and authorized state |
| POST | /api/v1/interviews/:id/plan | Generate/freeze structured plan |
| POST | /api/v1/interviews/:id/start | Start session, allocate quotas |
| POST | /api/v1/interviews/:id/events | Append candidate event idempotently |
| GET | /api/v1/interviews/:id/events | Stream/paginate transcript and timeline |
| POST | /api/v1/interviews/:id/finish | End and queue evaluation |
| GET | /api/v1/interviews/:id/report | Return rubric/evidence report after completion |
| POST | /api/v1/interviews/:id/voice-token | Issue scoped short-lived realtime token |
| POST | /api/v1/interviews/:id/code-runs | Run code with strict sandbox quotas |
| PUT | /api/v1/interviews/:id/whiteboard | Save versioned board state |
| DELETE | /api/v1/interviews/:id | Delete session data subject to stated retention/legal restrictions |
| GET | /api/v1/me/data-export | Export only owner's personal data |

**Future** endpoints for organizations, billing and reviewer APIs require separate auth, auditing and additional ADRs.

## Example session creation

\`\`\`json
{
  "role": "Backend Software Engineer",
  "seniority": "mid",
  "mode": "text",
  "duration_minutes": 20,
  "language": "en-US",
  "focus_areas": ["backend", "databases"],
  "source_document_ids": [],
  "consent": {
    "transcript": true,
    "audio_recording": false,
    "model_training": false
  }
}
\`\`\`

## Example event envelope

\`\`\`json
{
  "event_id": "evt-uuid",
  "session_id": "session-uuid",
  "sequence": 42,
  "kind": "candidate.answer.final",
  "occurred_at": "2026-11-13T09:00:00Z",
  "payload": {
    "text": "Use an exponential backoff and a circuit breaker.",
    "question_id": "q-003"
  }
}
\`\`\`

Server assigns canonical \`sequence\` and \`occurred_at\`; the client sends an idempotency token, not authoritative ordering, timestamps or scoring.

## Interview event kinds

- \`interview.started\`, \`interview.paused\`, \`interview.resumed\`, \`interview.completed\`
- \`interviewer.question\`, \`interviewer.follow_up\`
- \`candidate.answer.partial\` (transient), \`candidate.answer.final\`, \`candidate.skip\`
- \`code.run.requested\`, \`code.run.completed\`
- \`whiteboard.snapshot.saved\`, \`voice.connection.changed\`
- \`evaluation.started\`, \`evaluation.completed\`, \`evaluation.failed\`

## Report contract (conceptual)

\`\`\`json
{
  "session_id": "session-uuid",
  "rubric_version": "backend-mid-v1",
  "evaluation_status": "complete",
  "competencies": [
    {
      "key": "failure_handling",
      "score": 3,
      "scale_max": 5,
      "evidence_event_ids": ["evt-uuid"],
      "strengths": ["Identified circuit breaker"],
      "gaps": ["Did not address cache stampede"],
      "confidence": "medium"
    }
  ],
  "disclaimer": "Practice feedback; not a validated hiring decision."
}
\`\`\`

Only evaluator service may write canonical scores. The endpoint enforces user ownership and redacts hidden rubrics and provider credentials.

## Operational contract

- WebSocket/SSE for stream updates, heartbeat, backpressure and resume token; design with real voice provider.
- Avoid storing every interim STT token indefinitely; retain final segments by policy.
- Use optimistic concurrency \`version\` for whiteboard and session state.
- All API changes require versioned docs, contract tests and updated typed clients.
