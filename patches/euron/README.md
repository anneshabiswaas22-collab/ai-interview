# Candidate Euron Zod advisory fix

This is a reviewable patch for the **disposable upstream checkout**, not an imported or adopted application. It targets Euron commit `216a8fc52a055587f436f2446f1a80b6868bd14a` only. Keep the accompanying upstream MIT license when distributing this patch or upstream code.

`0001-zod4.patch` upgrades the API and web app from Zod 3.25.76 to 4.6.7 and updates the pnpm lockfile, including peer-resolution details, in response to [GHSA-mrhx-c7xc-m3w5](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5). Zod 4 is a major upgrade: validate behavior and compatibility before adoption; do not assume an empty advisory scan proves security.

## Local experiment

On Node 24 with the project's pnpm 9.15.0, the updated checkout passed `pnpm lint` (two existing warnings), `pnpm typecheck`, all 232 upstream `pnpm test` unit tests and `pnpm build`; `pnpm audit --prod` reported no known advisories. The patch was applied to a second clean checkout and its three files matched the tested checkout. These are preliminary results; Postgres/Redis integration and the offline browser demo must also pass on the patched checkout. No live provider, actual microphone or production environment was tested.

Apply the patch only in a disposable checkout:

```sh
git clone https://github.com/euron-sde-team/euron-open-real-time-ai-conversation-system.git euron
git -C euron checkout 216a8fc52a055587f436f2446f1a80b6868bd14a
git -C euron apply --unidiff-zero --check /absolute/path/to/0001-zod4.patch
git -C euron apply --unidiff-zero /absolute/path/to/0001-zod4.patch
cd euron
corepack pnpm install --frozen-lockfile
corepack pnpm audit --prod
```

The [verification workflow](../../.github/workflows/euron-zod-verification.yml) applies the exact patch, runs lint, typecheck, unit, production advisory and database integration checks, then runs the offline browser suite. The unmodified upstream signup test assumes immediate sign-in, so the browser job applies `scripts/diagnose_euron_signup.py` **only to the disposable test checkout** to follow the existing email-verification step. This does not mean the original upstream browser suite passed. Inspect the workflow result before treating the candidate patch as compatible.

Other adoption gaps remain: server-authoritative transcript/idempotency, evidence-grounded evaluation, privacy and consent, license/SBOM review and real-provider validation.
