# ADR 0004 — Deterministic, offline candidate profile and claim-grounded questions

**Status:** accepted (v2.0)

**Context.** Resume content is private and untrusted. The existing AI organiser can reword or, rarely, invent entries; generated
questions must be traceable to real statements.

**Decision.** Build the candidate profile from the user's saved profile with deterministic code: verify each entry against the raw
extracted text, derive confidence from evidence of use, flag clarification areas and injection-like text, and generate questions from a
reviewed catalogue of technology implications and a project deep-dive progression, each tied to its claim excerpt. No model call; the
existing AI question writer remains as an option. Offline questions follow the same per-resume cloud consent rule as AI questions,
because their excerpts accompany answers to the grader.

**Consequences.** Instant, free, private and testable; coverage is limited to the catalogue (~35 technologies and activities), which is
easy to extend in one file. Unknown technologies still get project deep-dive and clarification questions.
