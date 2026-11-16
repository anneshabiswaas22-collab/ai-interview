# Roadmap

This is a list of **intentions, not commitments**. There are no dates, and the project has one maintainer, so order and scope can
change. It is derived from the documented limitations in [README section 11](README.md#11-known-limitations) and from natural next
steps for the code base. Items tagged **[contributors welcome]** are good places to start; see [CONTRIBUTING.md](CONTRIBUTING.md).

Nothing here changes the project's principles: local-first by default, no telemetry, the application (not the model) decides scores
and state transitions.

## Verify what is only assumed today

- **Run on real Windows and Linux machines.** CI exercises the backend, frontend and launcher on all three systems, but the `.bat`
  wrappers, process start/stop on Windows and the Linux voice setup have not been run on real hardware. Reports of what works and
  what does not are valuable. **[contributors welcome]**
- **Measure grading quality of the 2.0 pipeline with the real `qwen3.5:4b` model.** The evidence and profile prompt was verified with
  a mocked model only. The plan is a small, labelled answer set (strong, partial, wrong, "I don't know", prompt-injection attempts)
  and a script that reports how the scores rank. **[contributors welcome]**
- **Test cloud mode against the real Ollama cloud service.** It has so far been verified against a fake server only, including cost
  estimates and the behaviour of reasoning models.
- **Try the microphone feature with a physical microphone** and different accents and Whisper sizes.

## Quality and maintainability

- **Static type checking for the backend** (mypy or pyright), introduced gradually so it does not block unrelated work.
  **[contributors welcome]**
- **Frontend component tests** for the Setup, Report and ResumeDetail pages (the current frontend tests cover helpers and a few
  components; the pages are exercised by the real-Chrome scripts in `frontend/e2e`). **[contributors welcome]**
- **Accessibility audit with a screen reader** (VoiceOver, NVDA). The existing sweeps check unnamed controls, contrast and overflow
  automatically; they do not replace listening to the interface. **[contributors welcome]**
- Keep the line-coverage figure honest: it was 94 % on 2026-11-15 and should not fall without a reason.

## Interview content

- **Extend the technology-implications catalogue** used for offline resume questions (about 35 technologies and activities today;
  others get project deep-dive and clarification questions only). Entries live in `backend/app/services/tech_implications.py` and
  must be reviewed for accuracy. **[contributors welcome]**
- Tune the adaptive engine's thresholds on real interview data. They are documented heuristics, not measured values.
- Revisit the short-phrase heuristic that suppresses follow-ups after "I don't know"-style answers.

## Distribution

- **Packaging** so users do not need Python and Node installed separately. This is an idea, not a plan; any packaging must keep
  the local-only guarantees and not add a silent update check.
- **First tagged release.** There are no git tags or published releases yet. The procedure is in
  [docs/maintainers/releasing.md](docs/maintainers/releasing.md).

## Not planned

- Telemetry, analytics or any call home.
- Multi-user accounts or a hosted service. The app is single-user and binds to loopback only.
- Letting the model decide scores, limits or state transitions ([ADR 0001](docs/adr/0001-deterministic-scoring.md)).

## How items get added

Open a feature request or start a Discussion (if enabled). See [docs/community/templates.md](docs/community/templates.md) for the
feature-discussion format the maintainer uses.
