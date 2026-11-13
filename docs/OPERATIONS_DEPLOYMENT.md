# Deployment, Observability and Operations Plan

**Future plan only; nothing has been deployed from this repository.** Implement after the application foundation is audited and a real end-to-end slice passes tests.

## Environments

- **Local:** no paid provider required for basic contract/unit tests; use mocks explicitly labeled as mocks.
- **Staging:** isolated test accounts, safe synthetic fixtures and limited real provider keys to verify microphone/network interactions.
- **Production:** managed secrets, HTTPS, hard quotas, backups, monitoring and controlled rollouts.

## Planned components

Web/API service; PostgreSQL with migrations and backups; Redis/queue if justified by adopted foundation; interview worker; separate speech worker or managed LiveKit; isolated code runner; optional model inference GPU service. Use simple infrastructure before premature Kubernetes adoption.

## Observability

Minimum per-session metrics:
- Interview starts/completions, reconnects, errors, timeouts, lost transcripts
- Token counts, model/provider, STT/TTS seconds and estimated money cost
- p50/p95 first token, time-to-first-audio and turn completion latency
- Code execution runtime, timeouts, blocked attempts and queue depth
- Evaluation rubric version, human-reviewed disagreement and regression counts

Use OpenTelemetry with PII redaction; optionally Langfuse core for LLM traces. **Never log complete resumes, private prompts with keys, candidate raw audio or full identifying transcripts by default.**

## Reliability

- Health/readiness checks; rate limits; provider circuit breakers; bounded retries/backoff.
- Idempotency for session writes and metered actions; worker dead-letter/recovery strategy.
- Graceful text-only fallback if speech service is unavailable.
- Durable database backup and restoration drill with published RPO/RTO after tests.
- Versioned release, rollback, incident response owner and change log.

## Cost controls

Set max duration/turn/token limits per session, usage tracking by provider, caching of safe repeated static data, stop-on-quota and environment-specific spend caps. Do not assume self-hosted GPU inference is free; compare actual utilization and total ownership cost with hosted API options.

## Security prerequisites

Dependency/SBOM review; encryption; permission/tenant tests; isolated executor threat review; privacy notice and consent; secrets manager; logging audit; vulnerability disclosure and monitoring.

## Launch checklist

- [ ] Tests run with real providers, not only offline stubs
- [ ] Load and latency tests recorded
- [ ] Data deletion/export and consent tested
- [ ] Real code execution isolated and penetration-tested
- [ ] Privacy/security/license review signed off
- [ ] Model output and scoring claims checked by reviewers
- [ ] Backups and restore drilled
- [ ] Budget limits and alerts enabled
- [ ] Support and incident response plan documented

See [roadmap](ROADMAP.md), [quality](QUALITY_AND_TESTING.md), [security](SECURITY_AND_PRIVACY.md).
