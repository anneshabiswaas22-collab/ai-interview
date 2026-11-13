# Third-Party License and Ownership Audit

**Snapshot verified against GitHub metadata and selected repository LICENSE files on 2026-11-13.** Licenses and transitive dependencies can change; inspect the pinned revision of any imported code before shipping. This document is a tracking aid, **not legal advice**.

| Upstream | License observed | Note before copying |
| --- | --- | --- |
| [Euron](https://github.com/euron-sde-team/euron-open-real-time-ai-conversation-system) | MIT (GitHub repo metadata + README) | Keep license and copyright notices; audit bundled assets, dependencies and data |
| [DeepInterview](https://github.com/ngoanpv/DeepInterview) | Apache-2.0 (metadata + README) | Preserve LICENSE/NOTICE as applicable; inspect providers and assets |
| [GrillKit](https://github.com/Forkfield/grillkit) | Apache-2.0 (**LICENSE file verified**) | GitHub metadata returned NOASSERTION; actual LICENSE declares Apache 2.0. Judge0 integration has its own terms |
| [Piston](https://github.com/engineer-man/piston) | MIT (metadata) | Self-hosting restrictions/secure sandboxing are separate questions |
| [Excalidraw](https://github.com/excalidraw/excalidraw) | MIT (metadata) | Embedded assets and any dependencies must also be reviewed |
| [LiveKit Agents](https://github.com/livekit/agents) | Apache-2.0 (metadata) | Hosted LiveKit may have service fees |
| [Promptfoo](https://github.com/promptfoo/promptfoo) | MIT (metadata) | Review dependencies and any separately distributed packages |
| [Langfuse](https://github.com/langfuse/langfuse) | MIT core with separately licensed enterprise directories (**LICENSE file verified**) | Exclude/review enterprise paths such as `ee/`; core may be embedded/self-hosted under its license |
| [Unsloth](https://github.com/unslothai/unsloth) | Apache-2.0 core (metadata) | Optional Studio UI/packages may have separate licenses; audit exact installs |
| [vLLM](https://github.com/vllm-project/vllm) | Apache-2.0 (metadata) | Model **weights** have independent license terms |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Pending pinned-source verification | Speech checkpoint licenses and redistribution rights may differ |
| [Qwen model family](https://huggingface.co/Qwen) | **Checkpoint-specific; verify before use** | Model weight terms, acceptance conditions, derivative and commercial rights depend on exact checkpoint |
| [Judge0](https://github.com/judge0/judge0) | GPL-3.0 noted in prior review; reverify pinned tree | Prefer Piston for simpler intended integration; evaluate copyleft obligations with counsel |
| [tldraw](https://github.com/tldraw/tldraw) | Production SDK terms require review | Not our default; use Excalidraw first |

## Principles

1. **Public GitHub != public domain.** Read each LICENSE and copyright/NOTICE.
2. **MIT/Apache ≠ exclusive ownership.** We may own *new original contributions* subject to arrangements, not relicense upstream source as if authored by us.
3. Keep a `THIRD_PARTY_NOTICES.md` when third-party code is actually imported. Do **not** invent attributions for components not yet present.
4. Record pinned commit SHA/tag, package source, license text, transitive dependency licenses and any generated assets.
5. Do not import premium interview questions, private resumes, production API keys or scraped proprietary products.
6. Vet model weights, datasets, voices and generated synthetic-data provenance independently.
7. Commercial deployment may require compliance for privacy, accessibility, payments, AI assessments and jurisdiction-specific employment rules.

## Current repository's license

**No license file has been added for our own original project yet.** A public repository without a license generally does not authorize unrestricted copying of original content. The owner should choose a documented project/contribution IP policy before accepting code from external contributors. MIT and Apache-2.0 apply to specified upstream projects only; they do not automatically license this repository.

## Required before first upstream import

- Select and pin exact base commit.
- Enumerate files and asset dependencies being copied.
- Preserve upstream LICENSE/NOTICE and modifications attribution.
- Run license and dependency scans; inspect SBOM and security advisories.
- Update this audit with proof and ask maintainer/legal review on any unclear rights.

_Last checked 2026-11-13; not a blanket approval to redistribute every upstream asset._
