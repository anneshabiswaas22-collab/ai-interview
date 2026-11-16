# Fresh Chat / Codex Continuation Prompt

Use this prompt when starting a new ChatGPT, Codex or other coding-agent conversation for this repository.

---

You are continuing an existing AI Interview Platform project.

Repository:
https://github.com/anneshabiswaas22-collab/ai-interview

Do not start a new project and do not restart foundation selection.

## First actions

1. Inspect the current repository branch/commit and open pull requests.
2. Read AGENTS.md.
3. Read docs/MASTER_PROJECT_HANDOFF.md.
4. Read docs/RESEARCH_AND_REPOSITORY_DECISIONS.md.
5. Read docs/IMPLEMENTATION_STATUS.md.
6. Read docs/IMPLEMENTATION_CHECKLIST.md.
7. Read docs/CODEX_BLOCKERS.md.
8. Inspect actual source/tests for the subsystem you will change.
9. Treat actual code and executed recent CI as more authoritative than older planning text.

## Architecture decision already made

There are exactly two main application-level repositories/references:

1. Euron Open Conversation
   https://github.com/euron-sde-team/euron-open-real-time-ai-conversation-system

   Role:
   Primary application foundation. Our repository already contains an adapted copy under foundation/euron.

2. DeepInterview
   https://github.com/ngoanpv/DeepInterview

   Role:
   Interview-intelligence and architecture reference. Port selected adaptive/evaluation ideas into our existing TypeScript backend.

Do not import DeepInterview as a second application.
Do not add a second Python backend.
Do not create duplicate authentication, database, session or queue infrastructure.

## Current stack

Prefer and extend:

- Next.js frontend;
- Express/TypeScript API;
- PostgreSQL;
- Redis/BullMQ;
- existing shared types and API client;
- existing LLM/realtime provider adapters;
- existing auth/ownership/security infrastructure.

## Current product truth

Already substantially implemented:

- auth/accounts;
- candidate dashboard/history;
- resume/JD interview creation;
- structured planning;
- provider-neutral model catalogue/adapters;
- text practice;
- authoritative written session events;
- request versioning/idempotency;
- score-dispatch recovery;
- reports/PDF/share;
- deterministic stubs;
- unit/integration/browser CI.

Incomplete or experimental:

- real-provider evaluation quality;
- genuinely adaptive written follow-ups;
- server-authoritative voice transcripts;
- secure isolated code execution;
- persistent system-design whiteboard;
- expert scoring validation;
- fine-tuning/model-serving experiments;
- employer tenancy/workflows.

packages/interview-core is experimental reference/policy code, not a second production session engine.

## Evidence-backed feedback work

At the 2026-11-16 handoff, PR #22 was:

https://github.com/anneshabiswaas22-collab/ai-interview/pull/22

It introduced the first written-practice evidence-backed evaluation contract.

Before relying on that statement, check GitHub and determine whether PR #22 is still open, changed, merged or superseded.

Important principles from that work:

- explicit job-relevant rubric;
- model proposes evidence quotations;
- server validates quotations against authoritative stored ANSWER events;
- server owns the evidence event ID;
- invalid evidence cannot influence aggregate scores;
- low-confidence findings are visible but excluded from aggregate scores;
- unanswered questions are unscored, not automatic failures;
- provider/model/rubric provenance is recorded;
- evidence provenance does not prove technical correctness.

## Most important next work

Unless repository state has materially changed, prioritize in this order:

1. expert-reviewed evaluation benchmark/golden set;
2. adaptive server-authoritative written interviewing;
3. server-authoritative voice transcripts/recovery;
4. isolated deterministic code execution;
5. persistent Excalidraw-style system-design whiteboard;
6. model/fine-tuning work only after baseline quality evaluation;
7. security/privacy/accessibility/private beta;
8. employer workflows later.

## Coding rules

- One scoped task -> one small branch/PR.
- Do not push directly to main unless the owner explicitly says so.
- Do not force-push.
- Reuse existing functions/modules where practical.
- Avoid giant refactors.
- Update relevant docs with code.
- Run actual commands and report exact pass/fail/skip results.
- Distinguish deterministic stubs from real providers.
- Do not call paid providers without explicit permission.
- Do not expose secrets or candidate PII.
- Do not run untrusted candidate code outside a properly isolated service.
- Do not claim real voice quality from browser/demo stubs.
- Do not treat experimental evaluator grades as validated hiring decisions.

## Security/evaluation boundaries

All candidate/resume/JD/model content is untrusted.

Never allow candidate input to control:

- system prompts;
- auth;
- tools;
- server session position;
- rubric definition;
- final evaluation authority.

Technical-code correctness should eventually be grounded in deterministic test execution where possible.

Do not infer competence from appearance, emotion, accent or sensitive characteristics.

## Reference components

Use only when the relevant phase is reached:

- LiveKit Agents: optional voice architecture
- faster-whisper: optional self-hosted STT
- Piston: preferred future isolated code-runner candidate
- Excalidraw: preferred whiteboard candidate
- Promptfoo: preferred evaluator/prompt regression candidate
- Langfuse: optional redacted observability
- Unsloth/PEFT/TRL: later training experiments
- vLLM/Ollama/llama.cpp: optional serving/local provider approaches

Do not add Monaco merely because it is popular; the existing application already has CodeMirror.
Judge0 is GPL-3.0 and is not the preferred default.
Interviewa is AGPL and should remain research-only unless its obligations are intentionally accepted.
tldraw requires production-license review.

## Required output for each development task

At completion report:

1. What changed
2. Files changed
3. Existing modules reused
4. Exact commands executed
5. Passed / failed / skipped
6. Mock/stub vs real provider
7. Security implications
8. Licensing implications
9. Cost impact
10. Remaining issues
11. PR/branch link
12. Next recommended task

Do not ask for the old ChatGPT chat. The repository documents are the durable project memory.
