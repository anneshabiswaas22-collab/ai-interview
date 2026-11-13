# Proposed Data Model and Retention Boundaries

**Conceptual schema only, not existing database tables.** Adapt to Euron migrations if adopted. Prefer one PostgreSQL database and avoid duplicating entities across agent services.

## Major entities

| Entity | Key fields | Relationships / governance |
| --- | --- | --- |
| users | id, auth_subject, display_name, created_at | owner identity; never store passwords in custom app |
| profiles | user_id, interests, role preferences, accommodation settings | optional, user-editable |
| source_documents | id, owner_id, kind, encrypted_blob_ref, extracted_summary, expires_at | resume/JD; smallest retention possible |
| interview_templates | id, role, seniority, competency rubric ref, version | curated/original question plans |
| interviews | id, user_id, template_id, status, language, modality, duration, created_at | candidate-owned session |
| interview_plans | id, interview_id, model_version, prompt_version, rubric_version, encrypted_plan | server-only internal plan |
| interview_events | id, interview_id, sequence, kind, speaker, payload_ref, created_at | immutable/timestamped timeline |
| rubric_scores | id, interview_id, criterion, version, score, evidence IDs, confidence | evaluator-owned, not client-supplied |
| reports | id, interview_id, rubric_version, summary, recommendations | linked to exact event/model versions |
| code_submissions | id, interview_id, question_id, source_ref, language, test_results, run_id | encrypted and quota-controlled |
| whiteboards | id, interview_id, version, snapshot_ref, updated_at | user-authored, versioned |
| consent_records | id, user_id, interview_id, purpose, granted_at, revoked_at | separate recording/training consents |
| provider_usage | id, interview_id, provider, model, tokens, audio_seconds, cost_estimate | billing/cost telemetry, minimal PII |
| audit_events | id, actor, action, object_type, object_id, timestamp | append-only admin audit, no raw secrets |
| memberships (later) | organization_id, user_id, role | tenant-scoped authorization |
| organization_assessments (later) | organization_id, job_id, rubric_version, reviewer IDs | separately gated employer workflows |

## Conceptual relationships

\`\`\`mermaid
erDiagram
  USERS ||--o{ INTERVIEWS : starts
  USERS ||--o{ SOURCE_DOCUMENTS : owns
  INTERVIEWS ||--|| INTERVIEW_PLANS : locks
  INTERVIEWS ||--o{ INTERVIEW_EVENTS : logs
  INTERVIEWS ||--o{ CODE_SUBMISSIONS : receives
  INTERVIEWS ||--o{ WHITEBOARDS : contains
  INTERVIEWS ||--o{ RUBRIC_SCORES : evaluated_by
  INTERVIEWS ||--o{ REPORTS : produces
  INTERVIEWS ||--o{ PROVIDER_USAGE : meters
  USERS ||--o{ CONSENT_RECORDS : grants
\`\`\`

## Retention policy — proposed and requiring review

- Resumes/JDs: process in-memory if possible; otherwise encrypted temporary storage with short TTL and explicit deletion.
- Transcripts: opt-in retention to enable coaching history; user deletion/export with clearly communicated limits.
- Raw audio/video: **off by default**; separate express consent, independently managed TTL.
- Training datasets: no default reuse of candidate sessions. Require separate affirmative permission and provenance.
- Code and whiteboards: store only where needed for replay, feedback or candidate-requested history.
- Operational traces: no raw resumes, audio, prompts with secrets, or unnecessary candidate identifiers.
- Admin audit and financial records: document applicable legal retention obligations separately.

Do not hardcode numeric retention durations before policy/legal review; build per-category TTL configuration.

## Database integrity constraints

- \`interviews.user_id\` foreign key and indexed authorized lookup.
- Unique \`(interview_id, sequence)\` and \`event_id\`; idempotent writes.
- Optimistic version control for session and whiteboard state.
- References to immutable rubric/model/prompt versions in score and report.
- Restrict delete cascades to proper user ownership and legal retention rules.
- Durable outbox or equivalent for evaluation queued after session completion.

## Security

Use encryption in transit and at rest, secrets manager, strict tenant ownership, scoped tokens and fine-grained audit logging. Never expose hidden rubrics or provider credentials to the browser. Test for object-ID enumeration and authorization bypass.

See [API](API_CONTRACTS.md) and [privacy](SECURITY_AND_PRIVACY.md).
