# Voice, Coding and System Design Modules

**Design specification only — none of these modules currently runs in this repository.**

## 1. Real-time voice

### Reuse strategy

Check Euron's existing voice provider adapters before changing them. If independent self-hosted speech models or agent-level control are required, evaluate LiveKit Agents with STT → LLM → TTS adapters (e.g., faster-whisper, license-verified Kokoro). Do not introduce a second WebRTC stack unnecessarily.

### Essential behavior

- Candidate gives microphone permission; never record audio without separate consent.
- Partial and final caption events shown with speaker labels; text fallback always available.
- Automatic silence detection, clarification requests, candidate interruptions (barge-in).
- Mute, pause, stop, reconnect, device change, network loss, no microphone and provider failure.
- AI cannot continue billing speech after session quota/time cap.
- User speech is answer content, never instructions that can change authorization.
- Monitoring: provider and end-to-end latency, time-to-first-audio, WER sample checks, errors, cost per minute.

### Integration acceptance

Real microphone roundtrip, user interrupts TTS within measured window, disconnect/reconnect does not duplicate transcript, timed sessions finish, cloud fallback explicitly marked, privacy prompts accessible.

## 2. Coding interviews

### Reuse strategy

Keep an audited working code editor from Euron. If insufficient, embed Monaco. Add a **separate, hardened** Piston service; its public API is not a dependable free production backend. Build original role-specific test/rubric management and candidate evidence display.

### Execution trust boundaries

- Code is untrusted. Must never execute in API/web/worker process.
- Network egress denied by default; no host mounts, no secrets, no privileged Docker socket access.
- Strong per-run CPU, memory, process, execution time, output and storage quotas.
- Restrict allowed languages/runtime versions; pin images/packages; no user-supplied install scripts.
- Rate-limit, queue and authenticate executions; separate operational and grading testcases.
- Hidden tests never sent to candidate browser; deterministic scores stored server-side.
- Security reviewer must sign off container/sandbox isolation before public launch.

### Candidate UX

Problem statement, language selector, editor, console, visible tests, run/submit controls, time budget and explanations. Store code snapshots and results for later replay with user consent.

### Grading

Tests verify behavior; optional AI discusses time/space complexity, design tradeoffs and readable improvements. Model cannot override objectively failing tests to make code "pass".

## 3. System design whiteboard

### Reuse strategy

Embed Excalidraw as the drawing UI rather than building a canvas engine. Keep the board in a scoped interview session; persist versioned scene data and important snapshots with the transcript. Respect the Excalidraw distribution terms and internal asset notices.

### Interview behaviors

Allow candidate to draw boxes/connectors, annotate services, reason about scaling, security, latency, availability, data consistency, failure handling and tradeoffs. Agent asks follow-ups grounded in diagram content; where parsing is uncertain, explicitly ask candidate to explain.

### Evaluation

Score architectural reasoning evidence, not neatness, drawing style or manual dexterity. Offer text-only accommodation.

## Integration order

1. Establish text interview and event contract first.
2. Add voice once agent transitions/persistence are robust.
3. Add coding with isolation and deterministic tests.
4. Add whiteboard snapshots/replay.
5. Add premium features only after usability and regression tests.

See [architecture](ARCHITECTURE.md), [security](SECURITY_AND_PRIVACY.md) and [product requirements](PRODUCT_REQUIREMENTS.md).
