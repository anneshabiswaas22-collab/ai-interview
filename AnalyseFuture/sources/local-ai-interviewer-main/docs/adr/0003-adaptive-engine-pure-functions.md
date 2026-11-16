# ADR 0003 — Adaptive engine as pure functions inside the existing state machine

**Status:** accepted (v2.0)

**Context.** The existing interview lifecycle is a persisted state machine with compare-and-set transitions that already handles
duplicates, stale tabs, restarts and failed evaluations. Adaptive behaviour must not weaken those guarantees.

**Decision.** Keep one state machine. Add an `adaptive` mode in which the selected questions form a pool table, and implement the
engine (`services/adaptive.py`) as deterministic pure functions over a snapshot. The service calls it inside the transition's
transaction (`_activate_next`, `_apply`) and persists the decision, the engine state and an event log atomically. Fixed mode keeps its
exact code path.

**Consequences.** Every engine decision is unit-testable without a database or model, reproducible, and explained in plain words.
Restart recovery needs nothing new. The trade-off is a heuristic (scored fit function) rather than a learned policy; weights are
documented constants.
