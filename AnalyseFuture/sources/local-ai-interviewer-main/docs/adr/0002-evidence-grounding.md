# ADR 0002 — Ground the grader's claims in the candidate's words

**Status:** accepted (v2.0)

**Context.** The main failure mode in practice is the grader asserting a "misconception" the candidate never stated, or reporting an
incomplete answer as an incorrect one. A second model call to double-check would double latency on the target hardware.

**Decision.** In the same grading call, the model must cite short verbatim quotes as evidence. The app verifies each quote against the
answer (normalised substring, ordered fragments), treats a misconception as an error only when grounded, keeps ungrounded ones visible
but uncounted, and applies a small set of documented deterministic consistency rules (cap non-attempts, separate incomplete from
incorrect, lower confidence on contradictions). No extra model call.

**Consequences.** Mistakes are not fabricated into the record; uncertainty is surfaced. Quote verification proves existence, not
correctness of the judgement — documented as a limitation. Rules are conservative (e.g. the incomplete-vs-incorrect correction requires
≥ 2 correct points and no claimed error at all).
