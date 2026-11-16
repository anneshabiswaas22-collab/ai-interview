"""Interview Intelligence 2.0: evaluation profiles, deterministic weighted scoring and rubric versioning."""
import pytest

from app.schemas import DimensionScores, RubricSettings
from app.services import eval_profiles as ep
from app.services.evaluator import compute_score
from app.services.prompts import eval_schema_for


def dims(**kw) -> DimensionScores:
    base = dict(correctness=8, completeness=6, depth=4, practical_application=3, clarity=9, production_awareness=2)
    return DimensionScores(**{**base, **kw})


@pytest.mark.parametrize("topic,text,itype,expected", [
    ("SQL", "anything", "technical", "sql"),
    (None, "Write a query with a LEFT JOIN and GROUP BY", "technical", "sql"),
    (None, "How do Python generators differ from lists?", "technical", "python"),
    (None, "How would you make an Airflow DAG idempotent?", "technical", "data_engineering"),
    (None, "Explain the bias-variance trade-off and overfitting", "technical", "machine_learning"),
    (None, "Design a URL shortener that scales to 1B links", "technical", "system_design"),
    (None, "How do you write a good unit test?", "technical", "software_engineering"),
    (None, "Tell me about a time you disagreed with a teammate", "mixed", "behavioral"),
    (None, "What is your greatest strength?", "hr", "behavioral"),
    (None, "What does a load balancer's strength lie in?", "technical", "system_design"),
    (None, "What is the capital of France?", "technical", "general"),
    ("Kafka Streaming", "x", "technical", "data_engineering"),
])
def test_category_detection_is_deterministic(topic, text, itype, expected):
    assert ep.detect_category(topic=topic, text=text, interview_type=itype) == expected


def test_general_profile_reproduces_the_v1_score_exactly():
    rubric = RubricSettings()
    for level in ("basic", "standard"):          # v1 had no "advanced" adjustment
        for prod in (True, False):
            for d in (dims(), dims(depth=9, practical_application=1, production_awareness=10), dims(correctness=2, clarity=10)):
                assert ep.score_answer(d, ep.get_profile("general"), rubric, level, prod).score == compute_score(d, prod, rubric, level)


def test_weights_are_normalised_and_reported():
    r = ep.score_answer(dims(conceptual_understanding=7, problem_solving=7, edge_cases=7), ep.get_profile("sql"), RubricSettings(), "standard", True)
    assert abs(sum(r.weights.values()) - 1) < 0.01 and r.missing_dimensions == []
    assert set(r.weights) >= {"correctness", "edge_cases", "conceptual_understanding"}


def test_dimension_not_scored_is_excluded_not_zero():
    full = ep.score_answer(dims(correctness=8, completeness=8, depth=8, practical_application=8, clarity=8, conceptual_understanding=8,
                                problem_solving=8, edge_cases=8), ep.get_profile("sql"), RubricSettings(), "standard", False)
    partial = ep.score_answer(dims(correctness=8, completeness=8, depth=8, practical_application=8, clarity=8), ep.get_profile("sql"),
                              RubricSettings(), "standard", False)
    assert full.score == partial.score == 8.0
    assert set(partial.missing_dimensions) == {"conceptual_understanding", "problem_solving", "edge_cases"}


def test_production_counts_only_when_relevant():
    d = dims(production_awareness=0)
    assert ep.score_answer(d, ep.get_profile("general"), RubricSettings(), "standard", False).score > \
        ep.score_answer(d, ep.get_profile("general"), RubricSettings(), "standard", True).score


def test_user_rubric_scales_every_profile():
    d = dims(correctness=10, completeness=2, depth=2, practical_application=2, clarity=2, tradeoffs=2, problem_solving=2, edge_cases=2)
    base = ep.score_answer(d, ep.get_profile("system_design"), RubricSettings(), "standard", False).score
    heavy = ep.score_answer(d, ep.get_profile("system_design"), RubricSettings(correctness=0.9), "standard", False).score
    off = ep.score_answer(d, ep.get_profile("system_design"), RubricSettings(correctness=0), "standard", False)
    assert heavy > base and "correctness" not in off.weights


def test_difficulty_awareness_basic_and_advanced():
    d = dims(correctness=9, completeness=9, clarity=9, depth=3, practical_application=3)
    p = ep.get_profile("sql")
    basic = ep.score_answer(d, p, RubricSettings(), "basic", False).score
    std = ep.score_answer(d, p, RubricSettings(), "standard", False).score
    adv = ep.score_answer(d, p, RubricSettings(), "advanced", False).score
    assert basic > std > adv


def test_behavioural_profile_never_asks_for_technical_extras():
    p = ep.get_profile("behavioral")
    assert p.extra_dimensions == [] and "production_awareness" not in p.weights
    block = ep.profile_prompt_block(p)
    assert "situation, task, action and result" in block


def test_profile_schema_requires_its_extra_dimensions_only():
    sql = eval_schema_for(ep.get_profile("sql").extra_dimensions)
    beh = eval_schema_for(ep.get_profile("behavioral").extra_dimensions)
    assert "edge_cases" in sql["properties"]["dimension_scores"]["required"]
    assert "edge_cases" not in beh["properties"]["dimension_scores"]["properties"]
    assert "evidence" in sql["required"] and "deeper_question" in sql["required"]
    keys = list(sql["properties"])
    assert keys.index("evidence") < keys.index("dimension_scores")      # quote before scoring


def test_rubric_fingerprint_is_stable_and_versioned():
    p = ep.get_profile("python")
    a, b = ep.rubric_fingerprint(p, RubricSettings()), ep.rubric_fingerprint(p, RubricSettings())
    c = ep.rubric_fingerprint(p, RubricSettings(depth=0.5))
    assert a == b and a != c and a.startswith(f"python-v{ep.PROFILES_VERSION}-")


def test_every_profile_is_described():
    out = ep.describe_profiles()
    assert {p["key"] for p in out} == set(ep.PROFILES) and all(p["dimensions"] for p in out)


def test_general_profile_is_v1_even_on_advanced_questions():
    d = dims(correctness=9, completeness=8, depth=3, practical_application=5, clarity=7, production_awareness=4)
    for prod in (True, False):
        assert ep.score_answer(d, ep.get_profile("general"), RubricSettings(), "advanced", prod).score == compute_score(d, prod, RubricSettings(), "advanced")


@pytest.mark.parametrize("text", ["Explain the transformer architecture", "How do you join a list of strings in Python?",
                                  "How do you index into a numpy array?", "What is regression testing?"])
def test_ambiguous_questions_fall_back_to_general(text):
    assert ep.detect_category(topic=None, text=text) == "general"
