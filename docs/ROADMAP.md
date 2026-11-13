# Delivery Roadmap and Milestone Gates

_No time estimates are guaranteed. Every milestone closes only after artifacts and acceptance criteria are satisfied._

## Milestone 0 — Documentation and contributor onboarding

**Deliverable:** README, AGENTS.md, complete project specifications, reuse/license assessment, contribution guide, initial issues. **Gate:** new contributor can identify the first build task without prior chat.

## Milestone 1 — Source-of-truth technical audit (do this first)

- Inspect and record Euron repository pinned commit, license/notices and architecture.
- Clone it in a disposable environment, install dependencies, run its existing tests and an offline demo.
- Separate stub/mock functionality from real model/voice behavior. Capture commands, logs and known gaps.
- Inspect DeepInterview and GrillKit for reusable ideas/code; compare license, quality, dependency conflicts.
- Validate Piston (sandbox isolation and API restrictions), Excalidraw, LiveKit, Promptfoo, Langfuse, Unsloth and serving stack.
- Write ADR selecting **base vs clean-room implementation** and a minimal migration path.
- Open an audit PR with test results and adjusted feature matrix. **Gate:** no unresolved critical security/licensing issue with chosen base.

## Milestone 2 — Candidate text interview vertical slice

- Adopt foundation after audit; stabilize build, database and auth.
- Role/seniority setup with optional JD/resume (consent + safe parsing).
- Typed interview plan, adaptive state machine, transcript events, timer and session resume.
- Rubric-based evaluator and persisted report with evidence links.
- Provider-neutral LLM interface, cost/latency telemetry and strict server-side prompt controls.
- E2E: create account → schedule/start → answer/probe → finish → feedback → reopen in history.
- **Gate:** tests, local instructions, no mocked success claims; defined performance baseline.

## Milestone 3 — Strong technical & voice practice

- LiveKit voice worker with STT/TTS adapters, captions, user interruption and reconnection.
- Reuse or adapt editor; isolate Piston executor with severe resource/network limits; run tests and grade deterministically.
- Excalidraw whiteboard with snapshots and synchronized transcript.
- Coaching dashboard and practice plans.
- **Gate:** real audio tests, code sandbox threat tests, accessible text fallback.

## Milestone 4 — Model quality and ownership

- Curate and review permissioned multi-turn interview data and ground-truth rubrics.
- Build baseline tests using Promptfoo/human review; benchmark Qwen candidate against existing model choices.
- Reproducible Unsloth/TRL QLoRA scripts and **external GPU** training notebook, with data/version metadata.
- Serve through vLLM or efficient compatible server; canary, rollback and per-session billing metrics.
- **Gate:** held-out evaluation improves meaningfully without unacceptable latency/cost/regressions; otherwise keep base model.

## Milestone 5 — Secure public beta and commercial readiness

- Security and privacy review, data export/deletion, observability, accessibility, rate limits and disaster recovery.
- Deployment strategy, secrets management, database backups and infrastructure IaC.
- Pricing hypothesis and billing provider validation before payment integration.
- Invite controlled users, collect consented quality feedback, prioritize correctness and retention.
- **Gate:** security signoff, documented known limitations, production SLOs and support playbook.

## Milestone 6 — Employer platform (separate review)

- Tenant/org accounts and recruiter roles, candidate invites and structured review.
- Validate job-specific rubrics, monitor fairness/accessibility, offer reasonable accommodations and human review.
- No automated hire/reject or sensitive-trait inference; obtain jurisdiction-specific counsel.
- **Gate:** approved responsible assessment framework and real human oversight.

## Cross-cutting definition of done

- One scoped issue and an accepted design/ADR for major changes.
- Documentation updated, no third-party licenses violated, dependencies pinned.
- Tests added at correct layers; CI is green and results recorded.
- Candidate data redacted from logs; security and privacy checks complete.
- Feature can be demonstrated with actual integrations; demos/stubs explicitly identified.
- Costs, latency and failure modes observable; rollback considered.
- PR explains what is implemented, what is merely planned and what remains blocked.

## Suggested first PRs

1. Audit Euron/DeepInterview/GrillKit and record actual statuses.
2. Design stable API/data contracts and security threat model.
3. Implement simplest non-mocked text interview path.
4. Add evaluation fixtures and observability.
5. Add voice/coding/diagram systems one at a time.

See [credit optimization](CREDIT_OPTIMIZATION.md) before asking Codex to execute a large task.
