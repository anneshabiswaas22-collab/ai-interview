# Recovery checkpoint — 18 November 2026

This is the first executable recovery checkpoint, not completion of the master reconstruction task. No archive, extracted source, historical document or existing feature was retired. The changes repair and extend the running application before attempting a directory migration.

## Preserved baseline

- Repository: `darksarkar28-boop/ai-interview`; original local branch `work`.
- Original HEAD: `d2bed6f35367ac754b5364ef829db1de2def53bb`; original working tree clean.
- Recovery branch: `recovery/forensic-baseline-and-feedback`; protected main was not modified.
- Verified local backup outside the checkout: `/workspace/recovery-evidence/d2bed6f/`. `repository.bundle` records all available refs and complete local history; `git bundle verify` passed; cloning that bundle into `/tmp/recovery-restore-check` and running `git fsck --full` recovered the exact original HEAD without errors. The working-tree archive was read back and all 2,219 files matched `baseline-files.json` SHA-256 values. Baseline tree and full commit/stat records are retained there. Backup files are read-only, not externally immutable storage.

| Artifact | SHA-256 |
| --- | --- |
| `repository.bundle` | `08ca97ae257eb7b00a20c890d76acf414b43522a6c4d7d1276ae94e18bc13e56` |
| `working-tree.tar.gz` | `37c8f0b0767f9f307f8f93cc5ac1eb01a0a5837f7f7f90423b0ce68be98f2147` |
| `baseline-files.json` | `35abd6984fad3fe2ff4ce5af09a866a75a5416395864c2f850bf8f78febbe219` |

The backup includes tracked and nonignored files; it is not a backup of secrets, dependency caches, Docker volumes, external deployments, GitHub settings or production user data. It is local to this cloud workspace and should be exported through an owner-controlled backup process before discarding the environment. Recovery can clone the bundle into a separate destination and read the archive there; never reset the current tree or overwrite existing work to test restoration.

## Investigation and recovery map

The bounded [security investigation](SECURITY_FINDINGS.md) found a complete 33-commit local ancestry, no dangling Git objects, and no evidence proving attacker attribution. Upload `a610107` added four ZIPs; later moves are traceable rather than proof that functionality was deleted. GitHub account logs, unavailable historical branches, external backups and hosted artifacts were not recovered. An author name alone cannot determine authorization.

All four archive checksums matched existing manifests; all 1,705 extracted file entries matched their ZIP bytes with no traversal or symlink entries. The [feature recovery matrix](FEATURE_RECOVERY_MATRIX.md) records concrete capabilities across all four sources, including valuable implementations, constraints and deferred integration. Twenty-seven isolated source grounding tests passed. A separate synthetic execution reproduced GrillKit's string-call coding-harness defect; it was not adopted into the active API.

| Original path | Current path | Responsibility | Evidence and action |
| --- | --- | --- | --- |
| `candidate/euron/` in history | `apps/interview-platform/` | Primary web/API, auth, database, jobs and provider adapters | Historical renames and current baseline tests; retain and repair in place |
| Four uploaded root ZIPs | `AnalyseFuture/archives/` | Original recovery inputs | Hash and extracted-byte verification; retain all |
| ZIP members | `AnalyseFuture/sources/` | Alternative implementations, tests, assets and legal provenance | Every entry inventoried; selective feature audit, not wholesale runtime adoption |
| `packages/interview-core/` | Same | Experimental session and evidence policy | 22 core tests; retain, do not create a second runtime authority |
| Local AI grounding and core evidence contract | `apps/interview-platform/apps/api/src/domain/text-evidence.ts` | Quotation provenance validation for the existing written scorer | Independent TypeScript implementation of the reviewed design; exact rather than normalized quotations, 42 adversarial validator cases |
| Existing written scorer/report path | Existing API worker, feedback JSON and report component | Integrated answer feedback | Persisted answer-event citations, null abstentions, safe share visibility; real PostgreSQL/Redis integration tests and React tests |
| Provider HTTP failure handling | Existing `integrations/http.ts` | Safe failure classification and metadata logging | Nine new privacy tests fail on baseline and pass after removal of raw response/exception logging |

The [file inventory and dependency graph](INVENTORY.md) cover every tracked and nonignored file with provisional responsibility, disposition, hashes and exact-byte matches. This accounts for files automatically; it does not claim every file was manually reviewed or that byte-identical files are safe to delete. Ignored local artifacts are counted without reading environment-file values. No ownership information was inferred from extensions alone.

## Implemented behavior and limits

Written feedback now flows through the existing consent/authentication, persisted answer events, scoring worker, provider adapters, feedback storage, API and report UI. Two server-defined criteria require exact answer-event quotations and linked observations. Invalid provider evidence fails closed; insufficient evidence remains null. The UI displays quotations as escaped text, links observations to them, distinguishes simulated feedback and explains that provenance does not prove correctness. Shares without transcript consent withhold the entire grounded feedback, including observations that could repeat private text. No new engine, provider call, dependency or database migration was added.

The provider-logging patch stops arbitrary upstream bodies and network exception messages entering logs while retaining failure classification. No actual disclosure of private user material was observed. This is a concrete hardening fix, not evidence identifying an attacker.

The baseline browser investigation also reproduced a signup verification race: a boot-time refresh without a cookie could clear a newer authenticated session. The scoped web fix preserves the newer session when that older empty/error response arrives. Deferred-response regression tests cover the race; the executed browser outcomes are recorded separately below.

Final validation passed 291 app unit tests, 22 core tests, 165 integration tests and all 9 browser tests, plus the 27 isolated source grounding tests. Lint, type checking, production builds, API specification, sanitization and inventory checks passed. Exact executed commands, baseline failures, post-change results, simulated-versus-real distinctions and browser runtime details are in [TEST_RESULTS.md](TEST_RESULTS.md). The actual ownership and rollback boundary are in [ARCHITECTURE.md](ARCHITECTURE.md).

## Reviewable implementation commits

| Commit | Scope |
| --- | --- |
| `782a957` | Provider error privacy fix and nine regressions |
| `02d0641` | Signup verification refresh race and three regressions |
| `9f18064` | Written evidence validation, scoring race guard, report integration and tests |

These commits are local on the recovery branch; nothing was pushed or deployed. Recovery inventory/report tooling is committed separately. Rollback should use normal reverts on a reviewed branch, not resets of the preserved baseline or deletion of runtime data.

## Outstanding work and safe continuation

1. Preserve and review this checkpoint before any bulk move or documentation retirement. Refresh inventory after further changes; do not delete provisional duplicates.
2. Validate real model feedback against expert-reviewed cases, including adversarial answers, uncertainty, correctness, quality and cost. Quotation validation is not prompt-injection immunity. External credentials and a budget remain prerequisites; none were activated.
3. Recover authoritative voice/provider events before trusting voice transcripts; test devices, interruption and reconnection with consent. Current voice simulation does not satisfy that requirement.
4. Plan separate tested slices for adaptive written follow-ups, resource-bounded document parsing, isolated code execution and whiteboard persistence. Existing editors and source algorithms are not proof these capabilities work securely.
5. Complete license, privacy, upload-resource, provider-destination and independent security reviews before public deployment. Owner-only account-security checks remain outstanding.
6. Only after feature ownership and regression evidence are sufficient, propose small structural moves with import/build/CI updates and reversible commits. Existing pnpm/Turbo workspace, auth authority and primary database remain the integration boundary.

No paid providers, GPU training, production deployment, purchase, force-push, original-source deletion, user-data deletion or external credential rotation was performed. Full recovery cannot be certified from the available source and local synthetic tests.
