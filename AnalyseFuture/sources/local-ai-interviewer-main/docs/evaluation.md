# How answers are evaluated (Interview Intelligence 2.0)

This document describes exactly what happens between "Submit answer" and the score you see. Every step below is implemented in
`backend/app/services/` and covered by tests in `backend/tests/`.

## Pipeline

```
answer saved (before any model call)
  │
  ├─ voice answer? → transcript repair (one small model call; falls back to the original text on any problem)
  │
  ├─ evaluation profile chosen by rules        eval_profiles.detect_category()
  ├─ ONE grading call, schema-constrained       prompts.eval_schema_for(profile)
  ├─ validation (Pydantic), one repair retry    evaluator._call_validated()
  ├─ grounding + consistency checks             grounding.ground()
  ├─ deterministic weighted score               eval_profiles.score_answer()
  ├─ follow-up decision (code, not the model)   evaluator.decide_followup() / adaptive.choose_followup()
  └─ stored with provenance                     Evaluation.provenance
```

No step adds a model call compared with v1: the profile, evidence and stretch question are part of the single grading call.

## 1. Evaluation profiles

Each question is graded with a profile picked **deterministically** (never by the model) from the interview type, the question's
topic and its text:

| Profile | Extra dimensions scored | Emphasis |
|---|---|---|
| General technical | — | identical to v1 weights (correctness 30, completeness 20, depth 15, practical 15, clarity 10, production 10) |
| SQL | conceptual understanding, problem-solving, edge cases | set semantics, NULLs, join/aggregation correctness |
| Python | conceptual understanding, problem-solving, edge cases | language semantics, idioms, error handling |
| Data engineering | problem-solving, edge cases, trade-offs | idempotency, incremental loads, late/duplicate data, cost |
| Machine learning | conceptual understanding, trade-offs | statistics, evaluation methodology, leakage |
| System design | problem-solving, edge cases, trade-offs (20 %) | requirements, architecture, scaling, failure handling |
| Software engineering | problem-solving, trade-offs | design, testing, maintainability |
| Behavioural | — (core dimensions re-defined) | relevance/credibility, STAR completeness, reflection, concreteness, structure |

Detection order: an HR interview → behavioural; an explicit topic alias (e.g. topic "SQL") → that profile; keyword rules on the topic,
then on the question text — every rule is scored by its number of distinct keyword hits and the best wins only when unambiguous (a tie
falls back to *general*, since a wrong profile is worse than a neutral one); otherwise *general*. In a technical interview, behavioural keywords in the question text are ignored.

The five core dimensions are always scored. Extra dimensions are requested only by the profiles above. If the model omits a requested
dimension it is **left out of the weighting** (and flagged), never treated as zero. `GET /api/evaluation/profiles` lists every profile
with its weights and meanings.

### Weights you control

The rubric editor in *Settings* still works for every profile: each of the six original dimensions is multiplied by
`your weight / default weight`. Doubling *correctness* doubles it everywhere; a weight of 0 removes that dimension everywhere.
Weights are re-normalised over the dimensions actually scored, and the normalised weights are stored with every evaluation.

### Difficulty awareness

- **Basic** questions (definitions; or difficulty *easy*): depth, practical application, edge cases and trade-offs count at 35 %
  (the v1 rule for depth and practical application, extended to the new dimensions).
- **Advanced** questions (difficulty *hard*, or the model's classification when you set none): in the category profiles, depth, edge
  cases, trade-offs and production awareness count 125 %. The general profile has no advanced adjustment.

The general profile reproduces v1 scores exactly at every level (tested in `test_eval_profiles.py`). **Questions that fall into a
category profile (SQL, Python, …) are scored with that profile's weights, so their scores can differ from v1** — this applies to fixed
and adaptive interviews alike, and the profile used is shown with every answer.

## 2. Evidence and grounding

The grader must back its analysis with **short verbatim quotes** from the answer (`evidence`). The app then checks them:

- A quote is **verified** only if it occurs in the answer after normalising case, punctuation and spacing (elided quotes with `...`
  must match fragment by fragment, in order; 1-word quotes prove nothing). For voice answers both the raw transcript and the repaired
  text are searched.
- A misconception counts as an **error** only if it is grounded: a verified "incorrect" quote supports it, or text it quotes is in the
  answer (content words, boilerplate such as "the candidate said" ignored). Ungrounded ones are kept and shown as *"possible errors — not found in your answer, not counted"*. They never make an answer
  "incorrect".

## 3. Consistency rules (deterministic)

| Situation | What the app does |
|---|---|
| short "I don't know"-style answer that the grader also found nothing of value in (no correct points, or correctness ≤ 4), scored above 2 | caps every dimension at 2; classified *no attempt*; no follow-up. A short real answer that merely contains "don't know" is not capped |
| Correctness ≤ 3 but ≥ 2 correct points, **no** claimed error of any kind, grader not unsure | raises correctness to 5 and says why: an incomplete answer is scored under completeness, not correctness |
| Correctness ≥ 8 with a verified error | confidence lowered to medium, flagged |
| Correctness ≥ 7 with nothing correct cited | confidence lowered to medium, flagged |
| Quoted evidence not found in the answer | quote marked unverified, flagged |

Every adjustment is written in plain words into the evaluation (`adjustments`, `consistency_flags`) and shown under *How this was graded*.

## 4. Classification

`correct` · `correct_incomplete` · `partially_correct` · `incorrect` · `no_attempt` · `uncertain` — computed by
`grounding.classify()` from the (adjusted) scores, grounded errors, correct points and confidence. An answer is only *incorrect* when
a grounded error exists (or nothing correct was said and correctness ≤ 2). A valid alternative approach with no grounded error cannot
be classified incorrect. Low grader confidence yields *uncertain* rather than a confident label.

## 5. Score and verdict

`score = Σ wᵢ·dᵢ / Σ wᵢ` over the scored dimensions, rounded to 0.1. Any total, verdict or classification the model volunteers is
ignored (tested). Verdicts: ≥9 Excellent, ≥7 Good, ≥5 Partial, ≥3 Weak, else Incorrect. Question and interview aggregation rules are
unchanged from v1 and printed in every report.

## 6. Reproducibility and provenance

Each stored evaluation records: `prompt_version` (currently `eval-2.0`), `profiles_version`, a `rubric` fingerprint
(`<profile>-v<version>-<hash of profile weights + your rubric>`), the question level, the model route (`graded_by`), the generation
temperature, and an `input_hash` (SHA-256 prefix of the exact grading messages — the hash, not the text). Identical input therefore
has an identical hash, so differing grades for the same input can be identified. Generation settings are the ones you configured
(`LLM_TEMPERATURE`, default 0.2); this release does not change them.

**Limits.** Grounding verifies that evidence *exists* in the answer, not that the grader's judgement about it is right; a small local
model can still be wrong on facts, especially without a reference answer. Treat scores as study feedback.

## 7. Report analytics

All computed in code from stored evaluations (`reports.intelligence()`): classification breakdown, difficulty-wise averages,
conceptual (correctness, conceptual understanding, depth) vs practical (practical application, problem-solving, edge cases, relevant
production awareness) averages, profile usage, evidence verification counts, consistency flags, a learning plan from the three
weakest skills, progress per topic versus the most recent earlier report covering it, the adaptive decision timeline and resume
coverage. Older reports without these fields still open.
