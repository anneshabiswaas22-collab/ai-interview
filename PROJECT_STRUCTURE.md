# Repository Structure and Ownership

The repository uses a conservative, reuse-first structure. Existing tested code stays in place while future boundaries are introduced incrementally.

```text
ai-interview/
├── apps/interview-platform/       # one runnable development candidate
├── packages/interview-core/       # experimental policy/evaluation library
├── docs/                          # categorized project source of truth
├── scripts/                       # repository-level validation tools
├── AnalyseFuture/                 # preserved, non-runtime research sources
├── .github/                       # CI and collaboration automation
└── PROJECT_STRUCTURE.md           # structure and ownership contract
```

## Ownership rules

- `apps/interview-platform` owns the current candidate UI, API, authentication, PostgreSQL schema, Redis jobs, provider adapters, reports, and local infrastructure.
- `packages/interview-core` is experimental until a documented decision reconciles it with the application's authoritative state model.
- `AnalyseFuture` owns preservation and analysis only. Nested applications are not workspace members, deployable services, or verified product features.
- New top-level `services/`, `ml/`, or `infrastructure/` directories should appear only when working, owned code justifies them. Do not create empty architecture theatre.

## Change policy

1. Preserve history, licenses, notices, locks, and evidence.
2. Prefer small adoption units over repository-wide copying.
3. Keep one source of truth for identity, sessions, data, and evaluation policy.
4. Update the feature/status documentation whenever behavior changes.
5. Separate simulated, mocked, integration, real-provider, device, and production evidence.

See [the preserved-source inventory](AnalyseFuture/SOURCE_INVENTORY.md) and [ADR 0003](docs/architecture/decisions/0003-candidate-foundation.md).
