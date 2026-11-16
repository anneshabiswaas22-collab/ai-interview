# ADR 0001 — The application, not the model, computes every score

**Status:** accepted (v1, extended in v2.0)

**Context.** Small local models (4B parameters on 8 GB machines) produce useful analysis but inconsistent totals; they also respond to
prompt injection in candidate text. Scores must be explainable and reproducible.

**Decision.** The model returns only validated, per-dimension 0–10 scores plus analysis. The application chooses the evaluation profile
by rules, applies versioned weights (scaled by the user's rubric and the question level), and computes the total, verdict and
classification. Any total, verdict or classification the model volunteers is ignored. Each evaluation stores a provenance record
(prompt version, profile version, rubric fingerprint, model route, temperature, input hash).

**Consequences.** Scores are reproducible from stored dimension scores and weights; changing weights is a code/config change with a
version bump, not a prompt tweak. A profile's extra dimensions are optional in the contract so older evaluations and weaker models still
validate; a missing dimension is excluded from the weighting, never zero.
