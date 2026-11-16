"""Adaptive interview engine. Pure, deterministic functions: no database, no model calls, no randomness.

The interview service gives it a snapshot (the remaining question pool, what has been asked and how it went, the engine's own
persisted state, elapsed time) and it returns a decision with a plain-language reason. The service persists the decision and
applies it inside the same transaction as the state change, so a crash can never leave a half-applied decision.

Decisions
  * difficulty level  - beginner | intermediate | advanced | expert. Changes only on the evidence of >= 2 scored answers since the
                        last change (a cool-down that prevents oscillation), weighted by the grader's confidence; two skips in a row
                        lower it. Never moves more than one level at a time.
  * next question     - every pool question is scored for fit (difficulty distance to the target level, the strategy's topic
                        preference, coverage of unexplored topics or resume claims, a single revisit of a weak topic); near-duplicates of
                        anything already asked are excluded. Ties are broken by the original pool order.
  * follow-up         - on top of the existing limit/duplicate/non-attempt policy: probe a gap, clarify an uncertain answer,
                        deepen a strong one (stretch question) or ask for a practical scenario; stops when probing stopped adding evidence.
  * end               - time limit, question limit, empty pool, or every planned topic has sufficient evidence.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

LEVELS = ["beginner", "intermediate", "advanced", "expert"]
LEVEL_DIFFICULTY = {"beginner": "easy", "intermediate": "medium", "advanced": "hard", "expert": "hard"}
DIFF_RANK = {"easy": 0, "medium": 1, "hard": 2}
STRATEGIES = ["progressive", "deep_dive", "practical", "conceptual", "mixed", "resume"]

RAISE_AT, LOWER_AT = 7.5, 4.5           # weighted recent average needed to move up / down
COOLDOWN = 2                            # scored answers needed since the last level change
REVERSAL_COOLDOWN = 4                   # ... before reversing the direction of the last change (stops up/down/up oscillation)
WINDOW = 3                              # most recent scored answers considered
CONF_WEIGHT = {"high": 1.0, "medium": 0.7, "low": 0.35}
TOPIC_EVIDENCE = 2                      # scored answers (not low-confidence) that make a topic "assessed"
MIN_QUESTIONS_BEFORE_EARLY_END = 4
UNCATEGORIZED = "General"

PRACTICAL_RE = re.compile(r"\b(how would you|design|build|implement|debug|troubleshoot|production|scenario|walk me through|optimi[sz]e|scale|handle|in practice|real.world|suppose|imagine)\b", re.I)
CONCEPTUAL_RE = re.compile(r"\b(what is|what are|explain|why|difference between|define|compare|meaning of|how does|concept)\b", re.I)


@dataclass
class PoolQ:
    id: int
    order: int
    text: str
    topic: Optional[str]
    difficulty: Optional[str]
    source: str = "bank"
    claim_label: Optional[str] = None


@dataclass
class Asked:
    text: str
    topic: Optional[str]
    difficulty: Optional[str]
    status: str                          # answered | skipped | unanswered | active
    score: Optional[float] = None
    confidence: str = "medium"
    source: str = "bank"
    claim_label: Optional[str] = None


@dataclass
class EngineState:
    level: int = 1
    scored_since_change: int = 0
    revisited: list[str] = field(default_factory=list)       # weak topics already revisited once
    focus_topic: Optional[str] = None
    level_history: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def load(cls, data: Optional[dict[str, Any]]) -> "EngineState":
        if not data:
            return cls()
        return cls(level=int(data.get("level", 1)), scored_since_change=int(data.get("scored_since_change", 0)),
                   revisited=list(data.get("revisited", [])), focus_topic=data.get("focus_topic"),
                   level_history=list(data.get("level_history", [])))

    def dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Settings:
    strategy: str = "progressive"
    max_questions: int = 10
    time_limit_s: Optional[int] = None
    focus_topic: Optional[str] = None


@dataclass
class Decision:
    action: str                          # ask | end
    kind: str                            # start | continue_topic | switch_topic | revisit_weak | explore_claim | revisit_claim | end_*
    reason: str
    pool_id: Optional[int] = None
    level_before: str = "intermediate"
    level_after: str = "intermediate"
    target_difficulty: Optional[str] = None
    topic: Optional[str] = None


def topic_of(t: Optional[str]) -> str:
    return (t or "").strip() or UNCATEGORIZED


# ---------------------------------------------------------------- difficulty
def update_level(state: EngineState, history: list[Asked]) -> tuple[EngineState, Optional[str]]:
    """Returns the new state and a reason when the level changed. Uses only answers given since the last change."""
    finished = [h for h in history if h.status in ("answered", "skipped")]
    since = finished[len(finished) - state.scored_since_change:] if state.scored_since_change else []
    # `scored_since_change` counts finished questions since the last change (kept by the caller via `record_finished`)
    recent_scored = [h for h in since if h.status == "answered" and h.score is not None][-WINDOW:]
    reason = None
    new = state.level
    last_two = [h for h in finished[-2:]]
    if len(last_two) == 2 and all(h.status == "skipped" for h in last_two) and state.level > 0 and state.scored_since_change >= 2:
        new = state.level - 1
        reason = "Two questions in a row were skipped, so the next one is easier."
    elif len(recent_scored) >= COOLDOWN:
        w = [CONF_WEIGHT.get(h.confidence, 0.7) for h in recent_scored]
        avg = sum(h.score * x for h, x in zip(recent_scored, w, strict=False)) / sum(w)
        low_conf = sum(1 for h in recent_scored if h.confidence == "low")
        if low_conf * 2 > len(recent_scored):
            return state, None                       # the evidence itself is unreliable: hold the level
        if avg >= RAISE_AT and min(h.score for h in recent_scored[-2:]) >= 6.5 and state.level < len(LEVELS) - 1:
            new = state.level + 1
            reason = f"Strong recent answers (weighted average {avg:.1f}/10 over {len(recent_scored)}), so the difficulty goes up."
        elif avg <= LOWER_AT and state.level > 0:
            new = state.level - 1
            reason = f"Recent answers averaged {avg:.1f}/10 over {len(recent_scored)}, so the next question is easier."
    if new != state.level and state.level_history:
        last = state.level_history[-1]
        last_dir = LEVELS.index(last["to"]) - LEVELS.index(last["from"]) if last.get("to") in LEVELS and last.get("from") in LEVELS else 0
        if last_dir and (new - state.level) * last_dir < 0 and state.scored_since_change < REVERSAL_COOLDOWN:
            return state, None                   # a reversal needs more evidence than a continuation
    if new != state.level:
        st = EngineState(level=new, scored_since_change=0, revisited=list(state.revisited), focus_topic=state.focus_topic,
                         level_history=[*state.level_history, {"from": LEVELS[state.level], "to": LEVELS[new], "after_question": len(finished), "reason": reason}])
        return st, reason
    return state, None


def record_finished(state: EngineState) -> EngineState:
    """Call once whenever a question finishes (answered or skipped)."""
    return EngineState(level=state.level, scored_since_change=state.scored_since_change + 1, revisited=list(state.revisited),
                       focus_topic=state.focus_topic, level_history=list(state.level_history))


# ---------------------------------------------------------------- evidence and coverage
def topic_stats(history: list[Asked]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for h in history:
        s = out.setdefault(topic_of(h.topic), {"asked": 0, "scores": [], "reliable": 0, "skipped": 0})
        s["asked"] += 1
        if h.status == "answered" and h.score is not None:
            s["scores"].append(h.score)
            if h.confidence != "low":
                s["reliable"] += 1
        elif h.status == "skipped":
            s["skipped"] += 1
    for s in out.values():
        s["average"] = round(sum(s["scores"]) / len(s["scores"]), 1) if s["scores"] else None
    return out


def topic_assessed(stat: Optional[dict[str, Any]]) -> bool:
    """Enough evidence on a topic: two reliable scores that agree (within 3 points), or three scored answers. Skips are not evidence."""
    if not stat:
        return False
    sc = stat["scores"]
    if len(sc) >= 3:
        return True
    return stat["reliable"] >= TOPIC_EVIDENCE and (max(sc) - min(sc) <= 3)


_FUNCTION_WORDS = {"what", "when", "where", "which", "why", "how", "would", "could", "should", "you", "your", "the", "and", "for", "with",
                   "use", "using", "does", "did", "are", "was", "were", "this", "that", "into", "from", "about", "explain", "describe",
                   "difference", "between", "tell", "give", "example", "can", "its", "their", "them", "have", "has"}


def _similar(a: str, b: str) -> bool:
    """Near-duplicate test on CONTENT words: "When would you use caching?" and "When would you use sharding?" are different."""
    if re.sub(r"\W+", " ", a.lower()).strip() == re.sub(r"\W+", " ", b.lower()).strip():
        return True
    x = {t for t in re.findall(r"[a-z0-9]+", a.lower()) if len(t) > 2 and t not in _FUNCTION_WORDS}
    y = {t for t in re.findall(r"[a-z0-9]+", b.lower()) if len(t) > 2 and t not in _FUNCTION_WORDS}
    return bool(x and y) and len(x & y) / len(x | y) >= 0.75


# ---------------------------------------------------------------- selection
def _focus(settings: Settings, state: EngineState, pool: list[PoolQ], history: list[Asked]) -> Optional[str]:
    if settings.strategy != "deep_dive":
        return None
    if settings.focus_topic:
        return settings.focus_topic.strip()
    if state.focus_topic:
        return state.focus_topic
    counts: dict[str, int] = {}
    for q in pool:
        counts[topic_of(q.topic)] = counts.get(topic_of(q.topic), 0) + 1
    return max(counts, key=lambda k: (counts[k], -min(q.order for q in pool if topic_of(q.topic) == k))) if counts else None


def _fit(q: PoolQ, *, target: str, settings: Settings, focus: Optional[str], stats: dict, last_topic: Optional[str],
         weak_topic: Optional[str], discussed_claims: set[str], weak_claims: set[str]) -> tuple[float, str]:
    """Higher is better. Returns (score, decision kind)."""
    score = 0.0
    kind = "continue_topic" if topic_of(q.topic) == last_topic else "switch_topic"
    d = DIFF_RANK.get((q.difficulty or "medium").lower(), 1)
    score -= 3.0 * abs(d - DIFF_RANK[target])
    t = topic_of(q.topic)
    seen = stats.get(t)
    s = settings.strategy
    if s == "deep_dive":
        score += 6.0 if focus and t.lower() == focus.lower() else -4.0
    elif s == "mixed":
        score += 3.0 if not seen else 0.0
        score -= 2.0 if t == last_topic else 0.0
    elif s in ("progressive", "practical", "conceptual"):
        score += 2.0 if not seen else (0.5 if not topic_assessed(seen) else -1.0)
    if s == "practical":
        score += 3.0 if PRACTICAL_RE.search(q.text) else 0.0
    if s == "conceptual":
        score += 3.0 if CONCEPTUAL_RE.search(q.text) and not PRACTICAL_RE.search(q.text) else 0.0
    if s == "resume":
        if q.source == "resume":
            score += 5.0
            if q.claim_label and q.claim_label not in discussed_claims:
                score += 2.0
                kind = "explore_claim"
            elif q.claim_label in weak_claims:
                score += 1.5
                kind = "revisit_claim"
    if weak_topic and t == weak_topic:
        score += 3.5
        kind = "revisit_weak"
    if topic_assessed(seen) and s != "deep_dive" and t != weak_topic:
        score -= 1.5                     # enough evidence already: spend the time elsewhere
    return score, kind


def decide_next(*, pool: list[PoolQ], history: list[Asked], state: EngineState, settings: Settings,
                elapsed_s: Optional[float] = None) -> tuple[Decision, EngineState]:
    """Choose the next question (or the end). `pool` = questions not yet asked; `history` = asked questions in order."""
    state, level_reason = update_level(state, history)
    level = LEVELS[state.level]
    base = {"level_before": level, "level_after": level}
    if level_reason and state.level_history:
        base["level_before"] = state.level_history[-1]["from"]
    asked = [h for h in history if h.status != "active"]

    if settings.time_limit_s and elapsed_s is not None and elapsed_s >= settings.time_limit_s:
        return Decision("end", "end_time", f"The {settings.time_limit_s // 60}-minute time limit was reached.", **base), state
    if len(asked) >= settings.max_questions:
        return Decision("end", "end_max", f"All {settings.max_questions} planned questions were asked.", **base), state
    candidates = [q for q in pool if not any(_similar(q.text, h.text) for h in history)]
    if not candidates:
        return Decision("end", "end_pool", "No unasked questions are left in the pool.", **base), state

    stats = topic_stats(asked)
    focus = _focus(settings, state, pool, history)
    if focus and state.focus_topic != focus:
        state = EngineState(level=state.level, scored_since_change=state.scored_since_change, revisited=list(state.revisited),
                            focus_topic=focus, level_history=list(state.level_history))
    # objectives satisfied: every topic still available has sufficient evidence (deep-dive: the focus topic)
    if len(asked) >= MIN_QUESTIONS_BEFORE_EARLY_END:
        remaining_topics = {topic_of(q.topic) for q in candidates}
        if settings.strategy == "deep_dive" and focus:
            fs = stats.get(focus)
            if fs and len(fs["scores"]) >= 4 and state.scored_since_change >= 2 and focus.lower() not in {t.lower() for t in remaining_topics}:
                return Decision("end", "end_objectives", f"The focus topic {focus} has been explored in depth.", **base), state
        elif (len(stats) >= 2 and UNCATEGORIZED not in remaining_topics and UNCATEGORIZED not in stats
              and remaining_topics and all(topic_assessed(stats.get(t)) for t in remaining_topics) and all(topic_assessed(s) for s in stats.values())):
            # only with real topic structure: an untagged or single-topic pool always runs to its question limit
            return Decision("end", "end_objectives", "Every planned topic has enough evidence for a reliable assessment.", **base), state

    last_topic = topic_of(asked[-1].topic) if asked else None
    weak_topic = None
    for t, s in stats.items():
        if t in state.revisited or s["average"] is None or s["average"] >= 5.0 or t == last_topic:
            continue
        if any(topic_of(q.topic) == t for q in candidates):
            weak_topic = t
            break
    discussed = {h.claim_label for h in asked if h.claim_label}
    weak_claims = {h.claim_label for h in asked if h.claim_label and h.score is not None and h.score < 5}
    target = LEVEL_DIFFICULTY[level]
    ranked = sorted(candidates, key=lambda q: (-_fit(q, target=target, settings=settings, focus=focus, stats=stats, last_topic=last_topic,
                                                     weak_topic=weak_topic, discussed_claims=discussed, weak_claims=weak_claims)[0], q.order))
    best = ranked[0]
    _, kind = _fit(best, target=target, settings=settings, focus=focus, stats=stats, last_topic=last_topic, weak_topic=weak_topic,
                   discussed_claims=discussed, weak_claims=weak_claims)
    if not asked:
        kind = "start"
    if kind == "revisit_weak":
        state = EngineState(level=state.level, scored_since_change=state.scored_since_change, revisited=[*state.revisited, weak_topic],
                            focus_topic=state.focus_topic, level_history=list(state.level_history))
    reason = _reason(kind, best, level=level, target=target, settings=settings, focus=focus, weak_topic=weak_topic)
    if level_reason:
        reason = f"{level_reason} {reason}"
    return Decision("ask", kind, reason, pool_id=best.id, target_difficulty=target, topic=topic_of(best.topic), **base), state


def _reason(kind: str, q: PoolQ, *, level: str, target: str, settings: Settings, focus: Optional[str], weak_topic: Optional[str]) -> str:
    t = topic_of(q.topic)
    diff = (q.difficulty or "unrated").lower()
    fit = f"{diff} question" + ("" if diff == target else f" (closest available to the {level} level)")
    art = "an" if fit[0] in "aeiou" else "a"
    return {
        "start": f"Opening with {art} {fit} on {t} at the {level} level.",
        "continue_topic": f"Staying on {t} with {art} {fit}" + (f" to explore {focus} in depth." if settings.strategy == "deep_dive" else "."),
        "switch_topic": f"Moving to {t} to cover another area, with {art} {fit}.",
        "revisit_weak": f"Returning to {weak_topic}, which went less well earlier, with {art} {fit}.",
        "explore_claim": f"Exploring a resume claim not yet discussed: {q.claim_label}.",
        "revisit_claim": f"Revisiting a resume claim that was explained weakly: {q.claim_label}.",
    }.get(kind, f"Next: {art} {fit} on {t}.")


def planned_total(settings: Settings, pool_size: int, asked: int) -> int:
    return min(settings.max_questions, asked + pool_size)


# ---------------------------------------------------------------- follow-ups
@dataclass
class FollowupChoice:
    ask: bool
    question: str = ""
    kind: Optional[str] = None           # probe_gap | clarify | deepen | scenario
    reason: str = ""
    suppressed_reason: Optional[str] = None


def choose_followup(*, gap_question: str, gap_reason: str, deeper_question: str, score: float, classification: Optional[str],
                    confidence: str, practical_score: Optional[int], strategy: str, level: str, used: int, max_followups: int,
                    previous_scores: list[float], is_followup_turn: bool, non_attempt: bool, too_similar) -> FollowupChoice:
    """Adaptive follow-up policy. The limits are the same hard limits as fixed interviews (enforced again at turn creation)."""
    if max_followups <= 0:
        return FollowupChoice(False, suppressed_reason="Follow-ups are disabled for this interview.")
    if used >= max_followups:
        return FollowupChoice(False, suppressed_reason=f"Follow-up limit reached ({used}/{max_followups}).")
    if non_attempt or classification == "no_attempt":
        return FollowupChoice(False, reason="No substantive attempt to build on.", suppressed_reason="The answer was not a real attempt.")
    if is_followup_turn and previous_scores and abs(score - previous_scores[-1]) < 0.5 and score < 7:
        return FollowupChoice(False, reason="Further probing on this point stopped adding new evidence.",
                              suppressed_reason="The last follow-up did not change the picture; moving on avoids a loop.")

    def ok(q: str) -> bool:
        return len(q.strip()) >= 8 and not too_similar(q)

    if confidence == "low" and gap_question and ok(gap_question):
        return FollowupChoice(True, gap_question.strip(), "clarify", "The grader was unsure what was meant, so a clarifying question helps.")
    strong = score >= 8 and classification == "correct"
    if strong and deeper_question and ok(deeper_question) and (strategy == "deep_dive" or level in ("advanced", "expert")):
        return FollowupChoice(True, deeper_question.strip(), "deepen", "A strong answer: a harder question checks the depth of understanding.")
    if gap_question and ok(gap_question):
        if strategy == "practical" and practical_score is not None and practical_score <= 5:
            return FollowupChoice(True, gap_question.strip(), "scenario", "The answer stayed theoretical; asking how it applies in practice.")
        return FollowupChoice(True, gap_question.strip(), "probe_gap", gap_reason or "Probing a concept the answer left out.")
    if gap_question:
        return FollowupChoice(False, reason=gap_reason, suppressed_reason="Follow-up repeated an earlier question or was too short.")
    return FollowupChoice(False, reason=gap_reason or "The answer gave enough evidence on this question.")
