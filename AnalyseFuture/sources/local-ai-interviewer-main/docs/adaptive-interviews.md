# Adaptive interviews

An interview runs in one of two modes:

- **Fixed** (default, unchanged since v1): the selected questions are asked in the chosen order.
- **Adaptive**: the selected bank questions and resume questions become a **pool**; after every finished question the adaptive engine
  (`backend/app/services/adaptive.py`) decides what to ask next, or that the interview is over, and says why.

The engine is a set of pure functions (no database, no model call, no randomness). The interview service gives it a snapshot and
persists its decision **in the same SQLite transaction** as the state change, so a crash never leaves a half-applied decision.

## Configuration (`InterviewConfig`)

| Field | Values | Notes |
|---|---|---|
| `mode` | `fixed` \| `adaptive` | |
| `strategy` | `progressive`, `deep_dive`, `practical`, `conceptual`, `mixed`, `resume` | adaptive only |
| `start_level` | `beginner`, `intermediate`, `advanced`, `expert` | maps to easy / medium / hard / hard |
| `max_questions` | 1–60 | adaptive: most main questions asked |
| `time_limit_minutes` | 5–240 or none | **both modes**: no new question starts after the limit; an answer in progress is still accepted and graded |
| `focus_topic` | text | deep-dive topic; default = the topic with most questions |
| `max_followups` | 0–3 | the same hard per-question limit as fixed mode |

`POST /api/interviews` also accepts `resume_auto: {resume_id, count}` to add claim-grounded questions built offline from a resume
(see [resume-intelligence.md](resume-intelligence.md)).

## Difficulty management

- Levels move **one step at a time** and only on evidence from **at least two scored answers since the last change** (cool-down),
  using the three most recent ones, weighted by the grader's confidence (high 1.0, medium 0.7, low 0.35).
- Up when the weighted average ≥ 7.5 and both of the last two scores ≥ 6.5; down when ≤ 4.5.
- If most of that evidence is low-confidence, the level is held.
- Two **skipped** questions in a row lower the level. Skips are never scores: they don't enter any average.
- **Reversing** the direction of the last change needs four answers instead of two, so alternating strong/weak answers (e.g. strong
  on medium, weak on hard) cannot make the level flip back and forth (tested).

## Choosing the next question

Every pool question gets a fit score; ties go to the original order:

- −3 per difficulty step away from the current level's target;
- strategy preference: *progressive/practical/conceptual* favour unexplored topics; *mixed* strongly favours unexplored topics and avoids
  repeating the last one; *deep_dive* strongly favours the focus topic; *practical* favours "how would you / design / debug /
  production" questions; *conceptual* favours "what / why / explain / compare" questions; *resume* favours resume questions about claims
  not yet discussed, then claims explained weakly;
- a topic that averaged below 5 is **revisited once**, after at least one other question;
- topics that already have sufficient evidence are de-prioritised;
- anything that duplicates a question already asked (same normalised text, or content-word overlap ≥ 0.75 — function words such as
  "when would you use" are ignored, so templated but different questions are kept) is excluded.

## When it ends

In order: time limit reached → question limit reached → no unasked question left → **objectives satisfied** (after at least four
questions, and only when at least two tagged topics were asked): every topic still in the pool, and every topic asked, has sufficient
evidence — two reliable (not low-confidence) scores within 3 points of each other, or three scored answers (skips are not evidence).
An untagged or single-topic pool always runs to its question limit. Deep-dive ends when the focus topic has ≥ 4 scored answers and no focus questions are
left. The reason is stored (`end_reason`) and shown in the report.

## Follow-ups

On top of the fixed-mode rules (limit, non-attempt, no repeats) the engine chooses the kind of follow-up from the single grading call:

| Kind | When |
|---|---|
| clarify | the grader was unsure (low confidence) |
| deepen | a strong, correct answer (score ≥ 8) at advanced/expert level or in a deep-dive: uses the grader's `deeper_question` |
| scenario | practical strategy and practical application ≤ 5 |
| probe gap | a missing concept or misconception |

**Loop guard:** if a follow-up answer scores within 0.5 of the previous answer on the same question (and below 7), probing stops —
it is no longer producing new evidence. Each follow-up decision is logged.

## Lifecycle and safety

Adaptive interviews use the same persisted state machine as fixed ones (`awaiting_answer → evaluating → (evaluation_failed) →
feedback → … → done`), with compare-and-set on `(status, phase, current turn)`:

- the answer is stored before the model is called and kept if grading fails (Retry);
- duplicate or stale submissions get HTTP 409 and change nothing;
- after a restart, an interview stuck in `evaluating` becomes `evaluation_failed` with the answer intact; the pool, level and decision
  log are in the database (`interview_pool`, `interviews.adaptive_json`, `adaptive_events`);
- paused time does not count toward the time limit (`paused_seconds`); time spent waiting for grading **does** count (the limit is
  wall-clock interview time), and the limit is checked when the next question would start. The feedback screen's "Next question"
  is a prediction; if the limit passes before you press it, the interview ends instead.

## What is stored

| Table / column | Content |
|---|---|
| `interview_pool` | the candidate questions, their original order, `available`/`used`, and the item each became |
| `interviews.adaptive_json` | engine state: level, answers since the last change, revisited topics, focus topic, level history |
| `interviews.plan_json` | topics to cover and, for resume questions, the roles/projects that could be discussed |
| `adaptive_events` | every decision: select / follow-up / end, with its reason, level before/after and topic |
| `interviews.end_reason` | `all_questions`, `ended_by_user`, `time_limit`, `end_time`, `end_max`, `end_pool`, `end_objectives` |

Unasked pool questions are not "unanswered": the report counts only questions actually asked.
