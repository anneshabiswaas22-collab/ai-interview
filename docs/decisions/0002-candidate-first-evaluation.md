# ADR 0002 — Candidate-first Coaching and Evidence-backed Evaluation

- **Status:** Proposed
- **Date:** 2026-11-13

## Context

The owner eventually wants to compete with both candidate-preparation and employer-assessment platforms. Hiring decisions are higher stakes and demand reliable, job-related scoring, fairness, accessibility, appeal paths and human oversight.

## Decision

1. Launch with **mock interviews and coaching** for consenting candidates; defer employer screening.
2. Separate live conversational agent from post-interview evaluator. Log rubric version and exact supporting evidence.
3. Prefer deterministic facts (coding tests, documented answer content) over subjective LLM impressions.
4. No facial expression, emotion, accent, disability or inferred personality scoring.
5. If employer workflows are introduced, require documented validity studies, human review, accommodation and applicable legal/privacy work.

## Consequences

- Better trust and clearer beta scope.
- Adds engineering for traceable scoring, prompt-injection testing, retention controls and evaluator disagreement.
- Avoids marketing practice scores as validated hiring decisions.

## Alternatives not chosen

Automated hire/no-hire decisions, proctoring by default and opaque 1–100 "fit" scores disconnected from rubric evidence.
