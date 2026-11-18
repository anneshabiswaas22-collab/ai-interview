# Recovery validation evidence

Run date: 18 November 2026 (Asia/Calcutta). Baseline source: `d2bed6f35367ac754b5364ef829db1de2def53bb`, branch `recovery/forensic-baseline-and-feedback`. Node `v22.23.5`, pnpm `9.15.0`, Linux. Every baseline source check below completed before recovery implementation edits began. Retained Docker images run the same baseline source. No archives or extracted source applications were executed.

## Baseline checks

Unless stated otherwise, working directory is `apps/interview-platform`, with `export PATH=/workspace/.onboarding-tools/node_modules/.bin:$PATH`.

| Command | Outcome | Evidence |
| --- | --- | --- |
| `node --test packages/interview-core/test/*.test.mjs` (repository root) | Passed: 22 tests, no skips | `/tmp/recovery-baseline-core.log` |
| `pnpm lint --force` | Passed: 6 tasks, no cached results | `/tmp/recovery-baseline-lint.log` |
| `pnpm typecheck --force` | Passed: 5 tasks, no cached results | `/tmp/recovery-baseline-typecheck.log` |
| `pnpm run test --force` | Passed: 233 tests (API 85, web 95, API client 29, UI 18, stubs 6); no cached results | `/tmp/recovery-baseline-test.log` |
| `TEST_DATABASE_URL=postgres://conv:conv@localhost:5512/conv_test TEST_REDIS_URL=redis://localhost:6449/1 pnpm test:integration` | Passed: 157 tests in 12 files, against real PostgreSQL/Redis and synthetic provider stubs | `/tmp/recovery-baseline-integration.log` |
| `pnpm build --force` | Passed: API bundle and Next.js production build; no cached tasks | `/tmp/recovery-baseline-build.log` |
| `pnpm openapi --check` | Passed: generated contract current, 81 operations | `/tmp/recovery-baseline-openapi.log` |
| `pnpm audit --prod` | Passed: no known vulnerabilities reported by registry audit at run time | `/tmp/recovery-baseline-audit.log` |
| `bash apps/interview-platform/scripts/test-sanitization.sh` (repository root) | Passed | `/tmp/recovery-baseline-sanitization-regression.log` |
| `bash apps/interview-platform/scripts/check-sanitization.sh` (repository root) | Passed: scanner clean; this is not proof that secrets never existed in history | `/tmp/recovery-baseline-sanitization.log` |

The integration setup explicitly refuses non-`_test` database names, recreates only `conv_test`, applies actual migrations, and clears Redis database 1. Existing local application data in `conv` and Redis database 0 were retained. No installation was needed; the verified onboarding dependencies were reused. A first `pnpm test --force` invocation was rejected by pnpm before tests ran because `--force` was interpreted as a pnpm option. The corrected explicit `pnpm run test --force` command above executed the complete suite.

## Running application smoke check

The retained stack was already healthy; no reseeding or account changes were performed. Local Python HTTP requests verified status 200 for `GET /api/ready` and the web root, then signed into the synthetic demo administrator using the existing ignored local password, and verified authenticated `GET /api/auth/me` and `GET /api/interviews`. Credentials and tokens were neither printed nor written to this report. This verifies local authentication and data access, not a complete candidate journey or provider quality.

## Browser checks

`PLAYWRIGHT_BROWSERS_PATH=/workspace/.playwright pnpm exec playwright install chromium` failed with HTTP 403 `Domain forbidden` for `cdn.playwright.dev`. This is a runtime network-policy restriction; the existing saved draft does not establish applied network access. Log: `/tmp/recovery-baseline-browser-install.log`.

The system already provides `/usr/bin/chromium` version `156.0.8078.79`. The existing full suite ran through a temporary `/tmp/recovery-baseline-playwright.config.ts` that imports the repository configuration and overrides only the browser executable, absolute suite/setup locations, list reporter, and output directory. Tracked Playwright configuration and test assertions remained unchanged. Command: `pnpm exec playwright test --config /tmp/recovery-baseline-playwright.config.ts`. **Baseline result: 8 passed, 1 failed** in 37 seconds. Log: `/tmp/recovery-baseline-e2e.log`. Passing coverage includes text practice with consent/reload/report, job-description planning, resume processing, coding editor flow, report sharing, admin quotas/permission denial, and accessibility.

To reproduce the system-browser fallback, create a temporary TypeScript config with the following contents (adjust the absolute checkout path if needed), then pass it to `pnpm exec playwright test --config <file>`:

```ts
import base from "/workspace/ai-interview/apps/interview-platform/e2e/playwright.config";
export default {
  ...base,
  testDir: "/workspace/ai-interview/apps/interview-platform/e2e/tests",
  globalSetup: "/workspace/ai-interview/apps/interview-platform/e2e/global-setup.ts",
  outputDir: "/tmp/recovery-baseline-e2e-results",
  reporter: [["list"]],
  use: { ...base.use, launchOptions: { executablePath: "/usr/bin/chromium" } },
};
```

The failed signup/verification browser test was rerun alone with `pnpm exec playwright test --config /tmp/recovery-baseline-playwright.config.ts e2e/tests/01-auth.spec.ts` and failed again with a fresh synthetic user. Trace inspection, without printing tokens/cookies, confirmed that email verification returned 200 and established the session, then the initial cookie-less boot refresh returned 204 slightly later and unconditionally erased the accepted session. The browser was redirected to login. This is a reproducible application race, not a missing browser or service prerequisite. Reproduction log: `/tmp/recovery-baseline-auth-repro.log`.

## Scope and limits

All model/realtime behavior in these local tests uses deterministic simulated providers. No real OpenAI/Gemini call, microphone/device test, GPU training, cloud deployment, production backup restore, external executor, or independent security review was performed. The passing audit reports only known advisories; it does not verify dependency authorship or absence of malicious logic. GitHub Actions configuration was inspected and local equivalents executed; no new hosted CI run was triggered. Temporary logs live on this task machine and are not a permanent external artifact store.

## Recovery implementation checks

Authentication recovery: `apps/interview-platform/apps/web/src/lib/auth.tsx` now clears a failed/empty boot refresh only if the session snapshot is still the one that request started with. An accepted login or verification session therefore survives a stale empty/network-failure result. `test/auth/provider.test.tsx` adds three deferred-response regressions: preserve the newly accepted session for late 204; preserve it for a late network error; retain normal clearing of an unchanged expired session.

- `pnpm --filter @open-conversation/web exec vitest run test/auth/provider.test.tsx`: **3 passed** (`/tmp/recovery-auth-regression.log`).
- `pnpm --filter @open-conversation/web typecheck`: **passed** (`/tmp/recovery-auth-typecheck.log`).
- `pnpm --filter @open-conversation/web exec eslint src/lib/auth.tsx test/auth/provider.test.tsx`: **passed** (`/tmp/recovery-auth-lint.log`).
- Prettier formatted only the changed authentication files; no assertions were removed or weakened.

- `bash scripts/codex-cloud-compose.sh up -d --build --no-deps --wait web`: **passed**, replacing only the web image/container and retaining all databases, accounts, baseline API/worker images (`/tmp/recovery-auth-web-build.log`).
- `pnpm exec playwright test --config /tmp/recovery-baseline-playwright.config.ts e2e/tests/01-auth.spec.ts`: **1 passed** in 6.9 seconds after the fix (`/tmp/recovery-auth-browser-fixed.log`). The unchanged test verified signup, email verification, dashboard landing, reload persistence, signout, wrong-password rejection and subsequent correct login. It had failed twice against the baseline. This confirms the recovered browser behavior with a fresh synthetic account; real providers are irrelevant to this authentication check.

The baseline full browser suite was not silently relabeled as passing: its original outcome remains 8 passed/1 failed. The later full-stack implementation checks above validate the recovery code separately.
