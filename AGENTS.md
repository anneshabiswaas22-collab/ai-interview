# AI Coding Agent / Codex Project Instructions

**Read this file before any implementation.** The repository includes a development-only candidate application. Do not claim working functionality until it has been executed and tested in this repository.

## Mission

Build the repository owner's independently branded, commercial-grade AI interview platform that can compete with Hello Interview, Final Round AI, Huru, CodeSignal and (later) employer assessment providers. Focus initially on software-engineering mock interviews, natural follow-ups, correct technical evaluation and personalized feedback. Optimize costs through mature open-source reuse.

## Mandatory reading order

1. [README](README.md) and [Vision](docs/VISION.md).
2. [PRD](docs/PRODUCT_REQUIREMENTS.md) and [Feature matrix](docs/FEATURE_MATRIX.md).
3. [Roadmap](docs/ROADMAP.md), [Architecture](docs/ARCHITECTURE.md), [Reuse vs build](docs/REUSE_VS_BUILD.md).
4. [License audit](docs/LICENSE_AUDIT.md), [Security](docs/SECURITY_AND_PRIVACY.md), [Contributor guide](CONTRIBUTING.md).
5. Relevant subsystem spec before editing it.

## Non-negotiable workflow

1. **Audit before implementation.** A pinned Euron candidate has been imported for development after source and runtime checks. Verify its actual features, tests, license and dependency quality; production approval remains gated by [ADR 0003](docs/decisions/0003-candidate-foundation.md).
2. **Do not blindly concatenate multiple repos.** Adopt one foundation only if audit justifies it. Reuse libraries via approved adapters/services, not extra whole apps.
3. **One scoped issue → one small PR.** Write intended changes, acceptance tests, security impacts and a rollback path. Avoid all-in-one enormous tasks.
4. **Prefer working components.** Inspect existing auth, parsing, editor, reports, queues and dashboards before rebuilding.
5. **Run real tests and record evidence.** State exactly which commands ran; distinguish stub, mock, integration, hosted provider, GPU training and production.
6. **Make no unapproved destructive changes.** Preserve history and current features, don't force-push, don't remove working code to make a template look neat.
7. **Update docs with code.** Feature matrix/status, dependencies, relevant ADRs and guides must match repository state.

## Technical boundaries

- Prefer modular monorepo with shared typed contracts; existing Euron stack unless a documented ADR selects otherwise.
- All user content, resumes, JDs and model outputs are untrusted. Never permit user input to set system prompts, tools, auth or scoring decisions.
- Only server-side evaluation may issue final rubric scores; deterministic code tests trump LLM guesses.
- Piston or an equivalent isolated executor must run untrusted code with quotas and no normal production-network access.
- Voice/STT/TTS/LLM providers replaceable, with budget limits and fallback; Colab/GPU training is **external**, not implied by Codex Cloud.
- Respect consent, deletion/retention, access controls, privacy and accessibility. Do not evaluate candidate competence from appearance, emotion, accent or other sensitive proxies.
- No covert assistance for live external interviews and no fully automated high-stakes hiring decisions.

## Credit optimization instructions

Before spending meaningful reasoning or coding time:
- Check exact feature status. Reuse or adapt rather than rewrite.
- Check dependency commercial license, maintenance and security.
- Avoid duplicate SDKs/queues/agents, premature infrastructure and large model training with no benchmark.
- Identify the smallest end-to-end slice that creates user value.
- Prefer targeted inspections and bounded test runs; summarize findings in a checked-in audit.
- Do not start a costly downstream stage (GPU, voice cloud, production deployment) without configuration, acceptance criteria and cost estimate.
- Use [docs/CREDIT_OPTIMIZATION.md](docs/CREDIT_OPTIMIZATION.md) to document tradeoffs.

## Definition of done

- Implementation matches acceptance criteria and is real, not a mock passing as real.
- Unit/integration/E2E/security tests run and results cited in PR.
- No secrets or candidate PII committed.
- Upstream license and notice requirements retained.
- Trace/quality/cost measurements defined where applicable.
- New contributor can reproduce the result from README/dev guide.

## First assigned action

**Current action:** extend the development candidate with evidence-backed feedback and real-provider evaluation using its existing auth and database. A text-practice slice has server-owned events and passed offline checks; voice still needs authoritative handling. Continue the license, security and real-provider reviews before any public use.

Read [docs/IMPLEMENTATION_CHECKLIST.md](docs/IMPLEMENTATION_CHECKLIST.md) and [docs/CODEX_BLOCKERS.md](docs/CODEX_BLOCKERS.md). Run the core unit tests and avoid duplicating policy engines when selecting Euron.

Document results and PR summary with: `What changed`, `Commands executed`, `Passed/failed/skipped`, `Real vs mock`, `Licensing`, `Costs`, `Remaining issues`.

This is the owner's vision and continuity document. Never ask a developer to locate an old ChatGPT discussion before proceeding.
