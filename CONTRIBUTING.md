# Contributing to AI Interview

Welcome! This repository is the source of truth for an AI interviewing project. It contains a development-only candidate application and specifications; do not assume planned capabilities are production-ready.

## 1. Learn the project in 15 minutes

- Start with [README.md](README.md), [vision](docs/VISION.md) and [requirements](docs/PRODUCT_REQUIREMENTS.md).
- Read [architecture](docs/ARCHITECTURE.md), [feature matrix](docs/FEATURE_MATRIX.md) and [roadmap](docs/ROADMAP.md).
- Before touching dependencies, read [reuse decisions](docs/REUSE_VS_BUILD.md) and [license audit](docs/LICENSE_AUDIT.md).
- For AI/Codex work, [AGENTS.md](AGENTS.md) is mandatory.

## 2. Find your first task

Review [implementation status](docs/IMPLEMENTATION_STATUS.md) and choose a scoped issue. The Euron development candidate is in `foundation/euron`; DeepInterview has not been imported.

Good early contributions:
- Verify upstream packages and test/demo instructions.
- Map actual vs claimed features, security and license risks.
- Write typed session/rubric contracts and tests once stack is chosen.
- Add evaluation fixtures with original, consented content.
- Create accessibility, abuse and sandbox threat-model test plans.

## 3. Development workflow

1. Discuss large changes in an issue and architecture decision record (ADR).
2. Create a branch named `feat/<short-scope>`, `fix/<short-scope>`, `docs/<short-scope>`, or `audit/<short-scope>`.
3. Make one coherent, reviewable change; avoid unrelated rewrites.
4. Add tests and documentation; update the feature matrix truthfully.
5. Use the PR template; include **commands actually run** and the observed results.
6. Request review; do not bypass review on risky changes, force-push shared branches or commit secrets.

## 4. Quality standards

- Stable typed contracts, strict input validation and permission checks.
- Tests for success, failure, timeouts, cross-user boundaries and retries.
- Open-weight AI is a provider choice, not a reason to skip quality benchmarks.
- No untrusted candidate code execution in the API process or unhardened Docker.
- No resume/recording uploads without proper consent, retention and access controls.
- Accessible, keyboard-usable design and text alternative to speech.
- Proportional data collection; no facial-emotion/accent/personality scoring.
- Label experimental AI judgments as feedback and keep human oversight for consequential decisions.

## 5. Third-party contributions and IP

The owner intends to run a product under their own brand and control. **A project license and contributor IP terms for the original code have not yet been selected.** Do not presume this repository is open-source just because it's public. Contact maintainers to agree on contribution/licensing terms before submitting external source-code contributions. Any imported MIT/Apache code must retain relevant attribution; different model/dataset/media terms apply separately.

## 6. Security reporting

Do not post real API keys, credentials, patient/candidate records, private resume contents, or exploitable production security details in public issues. Contact maintainers privately using available GitHub security reporting mechanisms before disclosure; see [security guidance](docs/SECURITY_AND_PRIVACY.md).

## 7. PR checklist

- [ ] Clear issue/acceptance criteria
- [ ] Build vs reuse decision captured
- [ ] Third-party licenses and dependencies reviewed
- [ ] Tests run and results (including failures/skips) provided
- [ ] No secrets/PII or unauthorized question-bank data
- [ ] README/docs/feature status updated
- [ ] Security, performance and costs considered
- [ ] Easy rollback or migration plan for significant changes

We optimize for a real high-quality interview experience, not a large diff or a high count of integrated repositories.
