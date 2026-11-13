# Codex / AI Engineering Credit Optimization

Owner priority: **stop using Codex credits to reimplement functionality already available in mature public software**. Credit optimization must not compromise reliability, licensing, privacy or maintainability.

## Before every Codex task

1. Name one **user-visible outcome** and one reproducible acceptance test.
2. Check this repository's [feature matrix](FEATURE_MATRIX.md) and recent commits/PRs.
3. Inspect relevant upstream feature, license, dependencies and concrete integration examples.
4. Choose: \`keep existing\`, \`install package\`, \`integrate separate service\`, \`adapt a small licensed module\`, or \`build original\`.
5. Estimate change radius, model/cloud service cost and risk of duplicated infrastructure.
6. Ask the agent to produce a short plan, then a **small working PR**, not a complete rebuild.
7. Stop and measure before a new provider or fine-tuning stage.

## Credit-saving rules

- **Do not rebuild** functional authentication, queue, report generator, parser, code editor or administrative UI without a documented defect/gap.
- **Do not clone and blend** Euron + DeepInterview + GrillKit as whole apps.
- **Do not train from scratch** or fine-tune without original datasets and a baseline quality benchmark.
- **Do not use GPUs** when CPU/unit fixtures can verify contracts.
- **Do not have multiple Codex agents** write overlapping modules without independent scope.
- **Do not redo market research** for every task; update one dated benchmark file.
- **Do not generate 100 placeholder features**; finish one end-to-end interaction and verify it.
- **Do not make UI redesigns repeatedly** before finalizing design tokens and flows.
- Keep **one stack and one interface per concern**, not many mutually exclusive abstractions.
- Use short, focused prompts referencing checked-in docs and exact files/issues.

## Suggested division of work

| Task | Tool | Cost control |
| --- | --- | --- |
| Product decisions and review | Human + issue/ADR | Clear gate and scope |
| Implement/test app | Codex Cloud | PR per bounded milestone |
| Audit public repository | Codex or reviewer | Record commit, commands, results once |
| Reusable libraries | pnpm/npm/pip packages | Pin versions and dependencies |
| LLM regression | Promptfoo + samples | Run cheap deterministic tests first |
| Fine-tuning | Colab/authorized GPU | Run only when dataset + evaluation complete |
| Production serving | GPU vendor/cloud | Measure spend per completed interview |
| Voice usage | Provider/local STT/TTS | Track seconds and per-session cap |

## Feature decision worksheet

Copy into an issue before coding:

\`\`\`text
Feature:
Existing implementation / tests:
User benefit:
Public reusable components + pinned versions:
Licensing / security risk:
Integrate vs build decision:
Smallest PR scope:
Acceptance steps:
What not to change:
Estimated external cost (if any):
Rollback and metrics:
\`\`\`

## Agent task example

"Read AGENTS.md, docs/ROADMAP.md, docs/REUSE_VS_BUILD.md. Audit only Euron's actual auth/plan/interview/report behavior at a pinned commit. Run documented tests. Output a factual gap matrix and ADR draft; do not rewrite the application, add dependencies or claim mocks are live providers. Commit audit docs and open PR."

## Measure engineering waste

Track number of redundant systems introduced, unverified claims corrected, PRs requiring rewrite, real test pass rate, integration defects, provider cost per interview and effort per completed acceptance test. Credit/token totals alone are not a measure of product quality.

**Goal:** Spend scarce reasoning effort on differentiated interview quality, technical evaluation and coaching, not infrastructure clones.
