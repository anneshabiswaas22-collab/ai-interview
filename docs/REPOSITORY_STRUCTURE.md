# Repository Structure and Ownership

The repository uses a conservative, reuse-first structure. Existing tested code stays in place while future boundaries are introduced incrementally.

```text
ai-interview/
├── foundation/euron/       # one runnable development candidate
├── packages/interview-core # experimental policy/evaluation library
├── docs/                   # product and engineering source of truth
├── scripts/                # repository-level documentation checks
├── AnalyseFuture/          # preserved, non-runtime research sources
├── .github/                # checks for docs, core, and candidate foundation
└── *.zip                   # untouched original source archives
```

## Ownership rules

- `foundation/euron` owns the current candidate UI, API, authentication, PostgreSQL schema, Redis jobs, provider adapters, reports, and local infrastructure.
- `packages/interview-core` is experimental until a documented decision reconciles it with the application's authoritative state model.
- `AnalyseFuture` owns preservation and analysis only. Nested applications are not workspace members, deployable services, or verified product features.
- New top-level `apps/`, `services/`, `ml/`, or `infrastructure/` directories should appear only as working code moves through small tested migrations. Do not create empty architecture theatre.

## Change policy

1. Preserve history, licenses, notices, locks, and evidence.
2. Prefer small adoption units over repository-wide copying.
3. Keep one source of truth for identity, sessions, data, and evaluation policy.
4. Update the feature/status documentation whenever behavior changes.
5. Separate simulated, mocked, integration, real-provider, device, and production evidence.

See [the preserved-source inventory](../AnalyseFuture/SOURCE_INVENTORY.md) and [ADR 0003](decisions/0003-candidate-foundation.md).
