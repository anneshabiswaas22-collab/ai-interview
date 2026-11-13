# Security, Privacy, Fairness and Responsible Assessment

**Policy blueprint; requires implementation, security review and applicable legal counsel before public deployment.**

## Data categories

Candidate identity/contact, resume/JD content, interview answers and transcript, optional audio, source code and diagrams, model prompts/tool traces, generated report and payment metadata. Treat all as sensitive candidate data; apply least privilege and appropriate retention.

## Consent and privacy

- Separate **necessary processing**, transcript storage, optional audio recording, analytics and *any training data reuse*. No bundling training consent into basic sign-up.
- Audio/video recording is **off by default**. Provide text-only alternative and a clear mic permission prompt.
- Publish a privacy notice and retention periods, deletion/export paths and contact for data requests.
- Minimize source resume retention; extract required context rather than storing entire file when possible.
- Redact names/emails/phone numbers and confidential project details from analytics/tracing.
- Do not pass private candidate data to external model providers without clear disclosure and appropriate agreements.
- Training on user sessions is disabled until consent, provenance, security and deletion policy are implemented.

## Authentication and authorization

- Use audited foundation auth; session lifecycle, secure cookie/token storage and CSRF protection.
- Server verifies owner/organization for every session/report/code/whiteboard/document object.
- Short-lived scoped tokens for realtime providers; never expose provider API keys to browser.
- Tenant isolation tests required before adding recruiter organizations.
- Rate limits, anti-enumeration controls, quota enforcement and abuse monitoring.

## Threat model (initial)

| Threat | Required protection |
| --- | --- |
| Prompt injection through resume, JD, answers or code comments | Treat all as untrusted content; strict tool scope; server-side system prompts; schema checks |
| Unauthorized report download | Object authorization on every request, expiring signed object URLs |
| Candidate falsifies score/usage/time | Server-owned rubric, event clock, quotas, billing and scoring |
| Remote-code execution through coding sandbox | Separate restricted host/service; unprivileged isolation, no egress/secrets, strict resource limits |
| Browser file uploads and parser attacks | File size/type validation, malware scanning where appropriate, safe parsing and storage |
| Cross-user transcript leakage | Row ownership checks, tests, encryption and non-guessable IDs |
| Third-party model data exposure | Approved processors, data-minimizing prompts, provider settings and deletion agreements |
| Long interview consumes unlimited GPU/voice | Hard per-session server quotas and provider timeouts |
| Supply-chain compromise | Pinned lockfiles, trusted releases, SBOM, dependency scanning, review |
| Candidate record leaks into LLM tracing | Redaction by default, sampled safe metadata, short retention |

## Assessment and fairness

- Candidate practice scores are **coaching feedback**, not psychometric validation.
- Explicit competency rubrics, link evidence and mark unknowns.
- No face/emotion inference, facial proctoring by default, accent penalty, demographic predictions or opaque "cultural fit" scores.
- Provide accommodations and alternate input modes. Avoid treating speech fluency as technical competence.
- Employer-grade assessment requires job-related validation, fairness studies, human review, appeal process and jurisdiction-specific counsel.
- Track evaluator drift, misleading score precision and potential disparate impacts with appropriate privacy safeguards.

## Security workflow

- Secrets via environment/secret manager, never in Git.
- Structured audit events with access restrictions; redact request bodies and raw LLM transcripts.
- Use trusted HTTPS, encryption at rest, backup/recovery testing and documented data lifecycle.
- Run SAST, dependency/license checks, penetration tests and prompt attack suite before beta.
- Maintain incident playbook: detect → contain → investigate → notify/restore as required.
- Public vulnerability reports should use a private GitHub security channel when available, not public issues with exploitable details.

## Open decisions

Jurisdictions, public privacy policy, retention schedule, legal basis, vendor DPAs, accessibility verification, optional proctoring and employee assessment governance. No one should declare them complete before validation.
