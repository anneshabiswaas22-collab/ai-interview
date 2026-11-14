# Developer Onboarding and Local Setup

The repository contains a development-only candidate application under [foundation/euron](../foundation/euron/README.md), plus a separate experimental interview-core package. The candidate is not production-ready; its default demo uses simulated model responses and scores. See [implementation status](IMPLEMENTATION_STATUS.md) and [the foundation decision](decisions/0003-candidate-foundation.md).

## Obtain the source

```bash
git clone https://github.com/anneshabiswaas22-collab/ai-interview.git
cd ai-interview
```

Read `README.md`, `AGENTS.md`, the foundation README and [third-party notices](../THIRD_PARTY_NOTICES.md).

## Run the candidate demo

Install Git, Docker with Compose v2, `make`, Bash and OpenSSL. Then:

```bash
cd foundation/euron
make up
make demo
```

Open `http://localhost:3550` and use the demo credentials printed by `make demo`. The first build downloads container images. Use synthetic information: the default provider is a deterministic stub, not a real AI evaluator. Camera proctoring is off in the demo user's default preferences.

`make ps` shows the stack. `make down` deletes the local demo volumes and their data; export anything needed first. Do not use these development settings for production.

## Run tests

For the standalone prototype, Node 22 or newer is sufficient:

```bash
node --test packages/interview-core/test/*.test.mjs
```

For the candidate application, install Node 22 and pnpm 9.15.0 through Corepack:

```bash
cd foundation/euron
corepack enable
pnpm install --frozen-lockfile
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm openapi --check
```

The [candidate foundation workflow](../.github/workflows/candidate-foundation.yml) also starts isolated PostgreSQL and Redis services for integration tests and runs the offline browser suite. Do not point tests at a real database: the integration guard requires a database name ending in `_test` and recreates it.

Real model and voice providers require separate configuration, consent, cost limits and testing. Do not commit keys, real resumes or recordings. The full application still needs the release gates in [ADR 0003](decisions/0003-candidate-foundation.md).
