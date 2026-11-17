# AnalyseFuture — Preserved Research Sources

This directory preserves every source archive supplied to the repository without treating it as part of the runnable product.

## Why this directory exists

The four ZIP files added by commit `a610107` remain byte-for-byte preserved under `archives/`. Their complete extracted contents are preserved under `sources/` so they can be inspected, compared, licensed, and selectively studied without overwriting the working application.

Nothing under `AnalyseFuture/sources/` is an active product dependency. Do not run, deploy, copy, or merge an archived application wholesale. The sources were inspected as untrusted research material and were not executed during this restructuring.

## Authoritative project structure

- `apps/interview-platform/` — the one development candidate application and current runtime foundation.
- `packages/interview-core/` — an experimental policy/evaluation package; not a second production engine.
- `docs/` — product, architecture, security, roadmap, and implementation source of truth.
- `AnalyseFuture/sources/` — untouched extracted research projects.
- `AnalyseFuture/archives/` — the original preserved ZIP archives.

## Preserved sources

- `sources/DeepInterview-main/`
- `sources/euron-open-real-time-ai-conversation-system-main/`
- `sources/grillkit-main/`
- `sources/local-ai-interviewer-main/`

See `SOURCE_INVENTORY.md` for the architecture, licensing, useful ideas, risks, and recommended disposition of each source. See `PROJECT_IDEA_AND_FUTURE_VISION.txt` for the consolidated product idea and long-term roadmap.

Integrity and complete file-purpose metadata are in [`inventory/`](inventory/README.md). The manifest and checksums cover every archive and all 1,705 extracted files without executing them.

## Adoption rule

An archived feature may enter the runnable product only through a scoped decision that records:

1. exact source and revision;
2. license and attribution obligations;
3. security and privacy review;
4. fit with the existing authentication, PostgreSQL database, Redis queue, and server-owned interview state;
5. tests proving the adopted behavior;
6. rollback and maintenance ownership.

The project must retain one primary application, one authentication authority, one session authority, and one primary database. A clean-looking directory tree is not a reason to discard tested code or merge several full applications.

## Repository recovery note

A local history inspection found no mass deletion or folder move in the latest upload: commit `a610107` added the four ZIP files and did not modify the earlier project tree. That evidence does not prove whether a GitHub account was compromised. The repository owner should separately review GitHub security logs, collaborators, deploy keys, webhooks, Actions secrets, personal access tokens, branch protection, and account sessions; rotate anything that may have been exposed.
