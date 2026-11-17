# ADR 0001 — Modular Monorepo, Reuse-First Architecture

- **Status:** Superseded for development use by [ADR 0003](0003-candidate-foundation.md); production review remains pending
- **Date:** 2026-11-13

## Context

Owner wants a custom commercial-grade AI interviewer, built with Codex/Astra and public components, while minimizing wasted coding credits and maintaining exclusive control of newly authored project code. Multiple existing interview apps cover overlapping concerns with incompatible stacks and dependencies.

## Decision

Maintain **one owned GitHub monorepo**. Consider Euron as primary starting application (MIT) after code/test/license/security audit. Study DeepInterview for conversational/voice agent design and GrillKit for technical exercise patterns. Prefer SDK integration (LiveKit, Excalidraw, Promptfoo, Unsloth) and isolated services (Piston, vLLM) instead of combining entire applications.

One authoritative auth/user database, one interview-state contract, one source of truth for scores and consent. Work incrementally.

## Consequences

- Lower redundant development, more maintainable boundaries and easier repo onboarding.
- Existing foundation may have hidden complexity; adoption still requires an audit.
- Some AI components and GPU serving incur ongoing operating costs.
- Reuse retains legal attribution and upstream licensing obligations.

## Alternatives rejected for now

- Single project without enhancements: important gaps around self-hosted AI/fine-tuning, coding safety and advanced coaching.
- Copy/merge all source trees: auth/dependency/DB/CI conflicts and higher maintenance.
- Entirely greenfield build: unnecessary reinvention and Codex expenditure.
- One large microservice for every framework: operations overhead before product validation.

## Review trigger

Revise if Euron audit reveals unacceptable quality/security/license issues, or integration cost exceeds a measured small greenfield alternative. Document specific evidence in a new ADR.
