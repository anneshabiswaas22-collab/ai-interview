"""Adaptive engine (pure functions): difficulty management, question selection, safeguards and follow-up policy."""
from app.services import adaptive as ad
from app.services.evaluator import too_similar

TEXTS = {
    ("SQL", "easy"): ["What is a primary key?", "What does GROUP BY do?"],
    ("SQL", "medium"): ["Explain INNER versus LEFT JOIN semantics.", "When would you add a composite index?"],
    ("SQL", "hard"): ["How would you fix a slow query scanning 500M rows?", "Design partitioning for a fast-growing events table."],
    ("Python", "easy"): ["What is a list comprehension?"],
    ("Python", "medium"): ["Explain how generators save memory."],
    ("Python", "hard"): ["Design a retry decorator with exponential backoff and jitter."],
    ("Spark", "medium"): ["How does Spark handle skewed joins?"],
}


def pool() -> list[ad.PoolQ]:
    out, i = [], 0
    for (topic, diff), texts in TEXTS.items():
        for t in texts:
            out.append(ad.PoolQ(id=i, order=i, text=t, topic=topic, difficulty=diff))
            i += 1
    return out


def asked(q: ad.PoolQ, score, status="answered", confidence="high", claim=None, source="bank") -> ad.Asked:
    return ad.Asked(text=q.text, topic=q.topic, difficulty=q.difficulty, status=status, score=score, confidence=confidence,
                    source=source, claim_label=claim)


def run(scores, *, strategy="progressive", start=1, max_q=20, confidences=None, focus=None):
    """Simulate an interview: the engine picks, the candidate scores as scripted. Returns (decisions, final state)."""
    p, hist, st = pool(), [], ad.EngineState(level=start)
    decisions = []
    s = ad.Settings(strategy=strategy, max_questions=max_q, focus_topic=focus)
    for i, sc in enumerate(scores):
        if i:
            st = ad.record_finished(st)
        d, st = ad.decide_next(pool=p, history=hist, state=st, settings=s)
        decisions.append(d)
        if d.action == "end":
            break
        q = next(x for x in p if x.id == d.pool_id)
        p.remove(q)
        conf = (confidences or {}).get(i, "high")
        hist.append(asked(q, sc if sc is not None else None, status="skipped" if sc is None else "answered", confidence=conf))
    return decisions, st, hist


def test_first_question_matches_the_starting_level():
    d, _, _ = run([None], start=0)
    assert d[0].kind == "start" and d[0].target_difficulty == "easy"
    d, _, _ = run([None], start=2)
    assert d[0].target_difficulty == "hard"


def test_one_strong_answer_does_not_change_the_level():
    d, st, _ = run([10, 10], start=1)
    assert d[1].level_after == "intermediate" and st.level == 1


def test_two_strong_answers_raise_the_level_once():
    d, st, _ = run([9, 9, 9], start=1)
    assert d[2].level_before == "intermediate" and d[2].level_after == "advanced" and "goes up" in d[2].reason
    assert st.level == 2 and st.scored_since_change == 0


def test_two_weak_answers_lower_the_level():
    d, st, _ = run([3, 2, 5], start=2)
    assert d[2].level_after == "intermediate" and "easier" in d[2].reason


def test_alternating_scores_do_not_oscillate():
    _, st, _ = run([9, 3, 9, 3, 9, 3, 9, 3], start=1)
    changes = st.level_history
    assert len(changes) <= 1


def test_cooldown_prevents_back_to_back_changes():
    _, st, _ = run([9, 9, 2, 9, 9], start=1)
    for a, b in zip(st.level_history, st.level_history[1:], strict=False):
        assert b["after_question"] - a["after_question"] >= ad.COOLDOWN


def test_low_confidence_evidence_holds_the_level():
    _, st, _ = run([9, 9, 9], start=1, confidences={0: "low", 1: "low"})
    assert st.level == 1


def test_two_skips_in_a_row_lower_the_level_and_skips_are_not_scores():
    d, st, hist = run([None, None, 7], start=2)
    assert d[2].level_after == "intermediate" and "skipped" in d[2].reason
    assert all(h.score is None for h in hist[:2])


def test_level_never_leaves_the_range():
    _, st, _ = run([10] * 12, start=3)
    assert st.level == 3
    _, st, _ = run([0] * 12, start=0)
    assert st.level == 0


def test_mixed_strategy_covers_topics_before_repeating():
    d, _, hist = run([7, 7, 7], strategy="mixed")
    assert len({h.topic for h in hist}) == 3


def test_deep_dive_stays_on_the_focus_topic():
    d, _, hist = run([7, 7, 7, 7], strategy="deep_dive", focus="SQL")
    assert {h.topic for h in hist} == {"SQL"}


def test_deep_dive_defaults_to_the_largest_topic():
    _, st, hist = run([7, 7], strategy="deep_dive")
    assert st.focus_topic == "SQL" and hist[0].topic == "SQL"


def test_practical_and_conceptual_strategies_prefer_matching_questions():
    _, _, hist = run([7], strategy="practical", start=2)
    assert ad.PRACTICAL_RE.search(hist[0].text)
    _, _, hist = run([7], strategy="conceptual", start=0)
    assert ad.CONCEPTUAL_RE.search(hist[0].text)


def test_weak_topic_is_revisited_once():
    p = pool()
    sql1 = next(q for q in p if q.topic == "SQL" and q.difficulty == "medium")
    py = next(q for q in p if q.topic == "Python" and q.difficulty == "medium")
    sp = next(q for q in p if q.topic == "Spark")
    hist = [asked(sql1, 3), asked(py, 7), asked(sp, 7)]
    rest = [q for q in p if q not in (sql1, py, sp)]
    st = ad.EngineState(level=1, scored_since_change=1)
    d, st2 = ad.decide_next(pool=rest, history=hist, state=st, settings=ad.Settings(strategy="mixed"))
    assert d.kind == "revisit_weak" and d.topic == "SQL" and "SQL" in st2.revisited
    hist.append(asked(next(q for q in rest if q.id == d.pool_id), 3))
    rest = [q for q in rest if q.id != d.pool_id]
    d2, _ = ad.decide_next(pool=rest, history=hist, state=st2, settings=ad.Settings(strategy="mixed"))
    assert d2.kind != "revisit_weak"


def test_never_asks_a_duplicate_or_near_duplicate():
    p = [ad.PoolQ(0, 0, "What is a primary key in SQL?", "SQL", "easy"), ad.PoolQ(1, 1, "What is a primary key in SQL databases?", "SQL", "easy")]
    hist = [asked(p[0], 7)]
    d, _ = ad.decide_next(pool=p[1:], history=hist, state=ad.EngineState(), settings=ad.Settings())
    assert d.action == "end" and d.kind == "end_pool"


def test_time_limit_and_question_limit_end_the_interview():
    p = pool()
    d, _ = ad.decide_next(pool=p, history=[], state=ad.EngineState(), settings=ad.Settings(time_limit_s=600), elapsed_s=600)
    assert d.action == "end" and d.kind == "end_time"
    d, _, _ = run([7, 7, 7, 7], max_q=2)
    assert d[-1].kind == "end_max"


def test_ends_when_every_topic_has_sufficient_evidence():
    p = [ad.PoolQ(i, i, t, "SQL", "medium") for i, t in enumerate(["Explain joins.", "Explain indexes.", "Explain transactions.",
                                                                    "Explain views.", "Explain triggers.", "Explain cursors."])]
    p += [ad.PoolQ(10, 10, "Explain generators.", "Python", "medium"), ad.PoolQ(11, 11, "Explain decorators.", "Python", "medium"),
          ad.PoolQ(12, 12, "Explain the GIL.", "Python", "medium")]
    hist = [asked(p[0], 7), asked(p[6], 7), asked(p[1], 7), asked(p[7], 7)]
    rest = [q for q in p if all(q.text != h.text for h in hist)]
    d, _ = ad.decide_next(pool=rest, history=hist, state=ad.EngineState(scored_since_change=1), settings=ad.Settings(strategy="mixed"))
    assert d.action == "end" and d.kind == "end_objectives"


def test_resume_strategy_explores_undiscussed_claims_first():
    p = [ad.PoolQ(0, 0, "Explain joins.", "SQL", "medium"),
         ad.PoolQ(1, 1, "How were failed Airflow DAG runs retried?", "Airflow", "medium", "resume", "Data Engineer at Acme"),
         ad.PoolQ(2, 2, "How did StreamWatch handle duplicate Kafka messages?", "Kafka", "medium", "resume", "StreamWatch"),
         ad.PoolQ(3, 3, "How did you cut Snowflake costs at Acme?", "Snowflake", "medium", "resume", "Data Engineer at Acme")]
    hist = [ad.Asked("How was the Acme pipeline monitored?", "Pipelines", "medium", "answered", 7, "high", "resume", "Data Engineer at Acme")]
    d, _ = ad.decide_next(pool=p, history=hist, state=ad.EngineState(), settings=ad.Settings(strategy="resume"))
    assert d.pool_id == 2 and d.kind == "explore_claim" and "StreamWatch" in d.reason


def test_decisions_are_deterministic():
    a = [x.pool_id for x in run([7, 4, 9, 9, 3, 6])[0]]
    b = [x.pool_id for x in run([7, 4, 9, 9, 3, 6])[0]]
    assert a == b


def test_state_round_trips():
    st = ad.EngineState(level=2, scored_since_change=1, revisited=["SQL"], focus_topic="SQL", level_history=[{"from": "a", "to": "b"}])
    assert ad.EngineState.load(st.dump()) == st and ad.EngineState.load(None) == ad.EngineState()


# ---------------------------------------------------------------- follow-ups
def fu(**kw):
    base = dict(gap_question="What happens to NULL keys in a join?", gap_reason="missing NULL handling", deeper_question="",
                score=6.0, classification="partially_correct", confidence="high", practical_score=6, strategy="progressive",
                level="intermediate", used=0, max_followups=2, previous_scores=[], is_followup_turn=False, non_attempt=False,
                too_similar=lambda q: too_similar(q, ["Explain joins."]))
    return ad.choose_followup(**{**base, **kw})


def test_followup_probes_a_gap():
    c = fu()
    assert c.ask and c.kind == "probe_gap"


def test_followup_clarifies_when_the_grader_is_unsure():
    assert fu(confidence="low").kind == "clarify"


def test_strong_answer_gets_a_deeper_question_at_high_levels_only():
    strong = dict(score=9.0, classification="correct", deeper_question="How would this change with a billion rows?", gap_question="")
    assert fu(**strong, level="advanced").kind == "deepen"
    assert not fu(**strong, level="beginner").ask
    assert fu(**strong, strategy="deep_dive", level="beginner").kind == "deepen"


def test_practical_strategy_asks_for_a_scenario():
    assert fu(strategy="practical", practical_score=3).kind == "scenario"


def test_followup_limits_and_non_attempts():
    assert not fu(max_followups=0).ask
    assert not fu(used=2).ask and "limit" in fu(used=2).suppressed_reason
    assert not fu(non_attempt=True).ask
    assert not fu(classification="no_attempt").ask


def test_followup_loop_guard_stops_probing_that_adds_nothing():
    c = fu(is_followup_turn=True, previous_scores=[5.0], score=5.2)
    assert not c.ask and "loop" in c.suppressed_reason


def test_duplicate_followup_is_suppressed():
    assert not fu(gap_question="Explain joins.").ask


def test_reversal_needs_more_evidence_than_a_continuation():
    """Fable's case: strong on medium, weak on hard. The level must not flip every two questions."""
    p, hist, st = pool() * 3, [], ad.EngineState(level=1)
    for i, q in enumerate(p):
        q.id, q.order = i, i
    s = ad.Settings(strategy="mixed", max_questions=16)
    for i in range(16):
        if i:
            st = ad.record_finished(st)
        d, st = ad.decide_next(pool=[q for q in p if q.text not in {h.text for h in hist}] or p, history=hist, state=st, settings=s)
        if d.action == "end":
            break
        q = next(x for x in p if x.id == d.pool_id)
        hist.append(asked(q, 8.5 if q.difficulty != "hard" else 4.0))
    flips = sum(1 for a, b in zip(st.level_history, st.level_history[1:], strict=False) if (a["to"] > a["from"]) != (b["to"] > b["from"]))
    assert len(st.level_history) <= 3 and flips <= 1


def test_untagged_pool_never_ends_early_on_objectives():
    words = ["caching", "sharding", "hashing", "queues", "retries", "logging", "tracing", "batching", "indexing", "pooling"]
    p = [ad.PoolQ(i, i, f"Explain {w} in depth", None, "medium") for i, w in enumerate(words)]
    hist = [asked(q, 8) for q in p[:5]]
    d, _ = ad.decide_next(pool=p[5:], history=hist, state=ad.EngineState(scored_since_change=1), settings=ad.Settings(max_questions=10))
    assert d.action == "ask"


def test_templated_but_different_questions_are_not_duplicates():
    assert not ad._similar("When would you use caching in a backend?", "When would you use sharding in a backend?")
    assert ad._similar("What is a primary key in SQL?", "what is a PRIMARY KEY in sql")
