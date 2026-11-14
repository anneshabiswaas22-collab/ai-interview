# Candidate application foundation

This directory contains an adapted development copy of Euron Open Conversation at commit `216a8fc52a055587f436f2446f1a80b6868bd14a`. Its MIT license is in [LICENSE](LICENSE); see [third-party notices](../../THIRD_PARTY_NOTICES.md). It is a provisional foundation for this project, not an approved production service.

The application includes a Next.js web app, Express API, PostgreSQL data store, Redis-backed jobs and provider adapters. The local demo uses deterministic stand-ins for the model and realtime interviewer. Its scores are scripted demonstrations, not evidence of candidate ability. Account controls, uploaded data, scoring and provider usage still need project-specific security and quality review before public use.

## Run the local demo

Requirements: Git, Docker with Compose v2, `make`, Bash and OpenSSL. From this directory:

```sh
make up
make demo
```

Open `http://localhost:3550` and sign in using the demo credentials printed by `make demo`. The first build downloads container images and may take several minutes. Use synthetic information. The demo user's preference for camera proctoring is off by default; a previously completed sample interview contains simulated proctoring events.

`make ps` shows local service status. **`make down` deletes the demo database and other local volumes**; export anything you need before running it.

## Test without production accounts

Node 22 and pnpm 9.15.0 are pinned by the project. After `corepack enable` and `pnpm install --frozen-lockfile`:

```sh
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

Database integration tests need isolated PostgreSQL and Redis services and must use a database whose name ends in `_test`; see `vitest.integration.config.mts`. The repository's [candidate foundation workflow](../../.github/workflows/candidate-foundation.yml) provisions test-only services and runs an offline browser suite. Check its actual results before treating a change as verified.

## Changes from the pinned upstream

- Updated Zod to 4.6.7 and regenerated the lockfile; account export is audited before data starts streaming.
- The browser signup test follows email verification when required.
- Default product name is `AI Interview`; the demo user's proctoring preference is off.
- The sanitization scanner handles loopback and documentation IP ranges correctly across awk implementations, with a regression check.
- Added a separate consent-based text-practice mode with server-selected questions, transactional history, safe answer retries and account export. Existing voice behavior remains a separate preview.
- Documentation and marketing assets not needed by the application were excluded from this copy.

## Practice by typing

Create an interview from a job description or resume, wait for its plan, and select **Practice by typing**. After consent, answer the saved questions. Responses and progress persist across reloads, and the report opens when the last question is submitted. A text interview cannot be switched to voice; create another interview for voice practice. The text mode does not use a camera or microphone and does not execute code. Text for a coding question is treated as a written explanation.

The demo's feedback is simulated. With a configured text provider, answers may be sent to that provider for feedback; no real-provider quality or cost validation has yet been completed. Feedback can be inaccurate, is not yet evidence-backed, and must not be used for hiring decisions. Deleting the interview removes its text-practice records; the account export includes them.

The existing [interview-core](../../packages/interview-core/README.md) remains an experimental policy module; it is not wired into this application. There must ultimately be one authoritative session and evaluation implementation. See [the adoption decision](../../docs/decisions/0003-candidate-foundation.md) for the integration and release gates.
