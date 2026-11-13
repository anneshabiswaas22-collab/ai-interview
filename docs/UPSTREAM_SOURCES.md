# Upstream Source Pins and Public Repositories

**GitHub branch head snapshot on 2026-11-13.** These are research/review references, not dependencies currently installed, and their HEADs may change after this snapshot. The reviewer must pin a specific revision in any actual integration and inspect the license text at that exact commit.

| Component | Repository | Observed branch commit | Stated license |
| --- | --- | --- | --- |
| Euron — candidate foundation | [euron-sde-team/euron-open-real-time-ai-conversation-system](https://github.com/euron-sde-team/euron-open-real-time-ai-conversation-system) | 216a8fc52a055587f436f2446f1a80b6868bd14a | MIT |
| DeepInterview — agents | [ngoanpv/DeepInterview](https://github.com/ngoanpv/DeepInterview) | bd6d136fffc509265bc2355e95101e0ad7f56eac | Apache 2.0 |
| GrillKit — technical practice | [Forkfield/grillkit](https://github.com/Forkfield/grillkit) | 15a400afb08349ad9b73f31a0c92ba147032164c | Apache 2.0 (LICENSE file) |
| Piston — code execution | [engineer-man/piston](https://github.com/engineer-man/piston) | de2b365ac759670a3a0d13ea208a0869a92c7e64 | MIT |
| Excalidraw — whiteboard | [excalidraw/excalidraw](https://github.com/excalidraw/excalidraw) | 82d5847e57dcb6fb5982833ea9ec2137fe0b2bd5 | MIT |
| LiveKit Agents — realtime voice | [livekit/agents](https://github.com/livekit/agents) | ae2e8a9a19d0302757dc2f1d34f93aa0377213fd | Apache 2.0 |
| Promptfoo — model tests | [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) | 803ff25776c445868fb46ac25eea0bc0d9969d97 | MIT |
| Langfuse — observability | [langfuse/langfuse](https://github.com/langfuse/langfuse) | 37f30667559d555234b5be86587450651883ddce | MIT core / restricted enterprise dirs |
| Unsloth — fine-tuning | [unslothai/unsloth](https://github.com/unslothai/unsloth) | 23ccb37dd627dd862eb6f67959b54eede1f78548 | Apache 2.0 core |
| vLLM — inference serving | [vllm-project/vllm](https://github.com/vllm-project/vllm) | 4dd68d139757b84757d126b7ca279e12d39e91e5 | Apache 2.0 |

## Other proposed references (commit/license not pinned here)

- [Monaco](https://github.com/microsoft/monaco-editor) — editor alternative only if audited existing editor is inadequate.
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — optional local STT.
- [Ollama](https://github.com/ollama/ollama) — local inference development.
- [Kokoro weights](https://huggingface.co/hexgrad/Kokoro-82M) — optional TTS; check exact voice/model license.
- [Qwen model family](https://huggingface.co/Qwen) — candidate base checkpoint; check checkpoint-specific terms.
- [Judge0](https://github.com/judge0/judge0) — consider copyleft/license and security implications before use.
- [tldraw](https://github.com/tldraw/tldraw) — evaluate production licensing if ever replacing Excalidraw.

## Upstream claims vs verified behavior

At the time of documentation creation, repository metadata, READMEs and selected LICENSE files were inspected. **No actual build/test/demo of these upstream applications was run as part of this documentation import.** Our own GitHub repository has no integrated app.

Euron's README describes voice interviewing through hosted OpenAI/Gemini providers, offline stub mode, resume/JD planning, reports/admin and tests. DeepInterview's README explicitly calls itself an early build with mock adapters and optional real-time provider worker. GrillKit's README describes coding functionality depending on Judge0.

Review before acting: [License audit](LICENSE_AUDIT.md), [Reuse vs Build](REUSE_VS_BUILD.md), [issue #1](https://github.com/anneshabiswaas22-collab/ai-interview/issues/1).
