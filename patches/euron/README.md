# Candidate Euron Zod advisory fix

This is a reviewable patch for the **disposable upstream checkout**, not an imported or adopted application. It targets Euron commit `216a8fc52a055587f436f2446f1a80b6868bd14a` only. Keep the accompanying upstream MIT license when distributing this patch or upstream code.

`0001-zod4.patch` upgrades the API and web app from Zod 3.25.76 to 4.6.7 and updates the pnpm lockfile, including peer-resolution details, in response to [GHSA-mrhx-c7xc-m3w5](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5). Zod 4 is a major upgrade: validate behavior and compatibility before adoption; do not assume an empty advisory scan proves security.

The first patched integration run passed 149 of 150 tests but exposed an export-audit race: the API ended the response before writing the audit record, so a client could receive the export before the record existed. The revised candidate patch records the access before streaming; an interrupted transfer is recorded as an export attempt. The existing integration test checks that the audit record exists when the response finishes. A new full run must pass before the fix is accepted.

## Local experiment

On Node 24 with the project's pnpm 9.15.0, the initial dependency-updated checkout passed `pnpm lint` (two existing warnings), `pnpm typecheck`, all 232 upstream `pnpm test` unit tests and `pnpm build`; `pnpm audit --prod` reported no known advisories. These are preliminary results; the revised patch's Postgres/Redis integration and offline browser demo must also pass. No live provider, actual microphone or production environment was tested.

## Try the local candidate demo

With Git, Docker Desktop or Docker Engine with Compose v2, `make`, and `openssl` installed, run this from the AI Interview repository. Choose a destination that does not already exist:

```sh
bash scripts/prepare_candidate_demo.sh ../euron-demo --start
```

When startup finishes, open `http://localhost:3550` and use the demo credentials printed by the script. It downloads a separate pinned checkout and applies the candidate dependency patch; it does not install the application into this repository. The local demo uses deterministic stand-ins and **does not provide real AI evaluation**. Use synthetic data. The upstream demo seed enables optional proctoring for one sample user, so check the setting before using the camera. The demo stack downloads images and can take several minutes to build.

To prepare the checkout without starting containers, omit `--start`.

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
