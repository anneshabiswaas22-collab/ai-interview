"""Evidence grounding, contradiction detection and answer classification (correct / incomplete / incorrect / ambiguous)."""
import pytest

from app.schemas import LLMEvaluation
from app.services import grounding as gr
from intel_fixtures import graded

ANSWER = "A LEFT JOIN keeps every row from the left table and fills NULLs where the right side has no match. It is slower than an inner join always."


def ev(score=7, **kw) -> LLMEvaluation:
    return LLMEvaluation.model_validate(graded(score, **kw))


@pytest.mark.parametrize("quote,ok", [
    ("keeps every row from the left table", True),
    ("KEEPS every row, from the LEFT table", True),             # case and punctuation do not matter
    ("keeps every row ... fills NULLs", True),                  # elision: fragments in order
    ("fills NULLs ... keeps every row", False),                 # wrong order
    ("keeps every column from the right table", False),        # not in the answer
    ("LEFT", False),                                            # too short to prove anything
    ("", False),
])
def test_quote_verification(quote, ok):
    assert gr.quote_in_answer(quote, [ANSWER]) is ok


def test_grounded_and_unverified_misconceptions_are_separated():
    e = ev(5, misconceptions=["Claims a left join is always slower", "Thinks joins delete rows"],
           evidence=[{"kind": "incorrect", "point": "left join always slower", "quote": "slower than an inner join always"}])
    g = gr.ground(e, answers=[ANSWER], non_attempt=False)
    assert g.grounded_misconceptions == ["Claims a left join is always slower"]
    assert g.unverified_misconceptions == ["Thinks joins delete rows"]
    assert any(f["code"] == "ungrounded_misconception" for f in g.flags)


def test_fabricated_quote_is_marked_unverified_and_flagged():
    e = ev(8, evidence=[{"kind": "correct", "point": "x", "quote": "uses a hash join under the hood"}])
    g = gr.ground(e, answers=[ANSWER], non_attempt=False)
    assert g.evidence[0].verified is False and any(f["code"] == "unverified_quote" for f in g.flags)


def test_misconception_quoting_the_answer_is_grounded_without_evidence_items():
    e = ev(5, misconceptions=['Said "slower than an inner join always", which is not generally true'])
    g = gr.ground(e, answers=[ANSWER], non_attempt=False)
    assert g.grounded_misconceptions and not g.unverified_misconceptions


def test_non_attempt_is_capped_and_classified():
    g = gr.ground(ev(6, correct=[]), answers=["I don't know"], non_attempt=True)
    assert g.classification == "no_attempt" and g.dimension_scores.correctness <= 2 and g.adjustments


def test_short_real_answer_with_dont_know_wording_is_not_capped():
    """'You don't know the length upfront, so use a generator.' is a correct answer, not an 'I don't know'."""
    g = gr.ground(ev(9, correct=["Generators avoid materialising the sequence"]), answers=["You don't know the length upfront, so use a generator."], non_attempt=True)
    assert g.dimension_scores.correctness == 9 and g.classification == "correct" and not g.adjustments


def test_unrelated_misconceptions_are_not_grounded_by_boilerplate_overlap():
    e = ev(5, misconceptions=["The candidate said that indexes slow down reads", "The candidate said that joins delete rows"],
           evidence=[{"kind": "incorrect", "point": "The candidate said that a left join is always slower", "quote": "slower than an inner join always"}])
    g = gr.ground(e, answers=[ANSWER], non_attempt=False)
    assert g.grounded_misconceptions == [] and len(g.unverified_misconceptions) == 2


def test_nothing_right_and_only_unverified_errors_is_uncertain_not_no_attempt():
    g = gr.ground(ev(1, correct=[], misconceptions=["claims something unprovable"]), answers=[ANSWER], non_attempt=False)
    assert g.classification == "uncertain"


def test_incomplete_is_not_reported_as_incorrect():
    e = ev(3, correct=["Says a left join keeps left rows", "Mentions NULL filling"])
    g = gr.ground(e, answers=[ANSWER], non_attempt=False)
    assert g.dimension_scores.correctness == 5 and g.classification != "incorrect"
    assert any(f["code"] == "incomplete_scored_as_incorrect" for f in g.flags)


def test_low_correctness_with_one_point_or_any_claimed_error_is_left_alone():
    assert gr.ground(ev(3, correct=["one point"]), answers=[ANSWER], non_attempt=False).dimension_scores.correctness == 3
    g = gr.ground(ev(3, correct=["a", "b"], misconceptions=["something unverifiable"]), answers=[ANSWER], non_attempt=False)
    assert g.dimension_scores.correctness == 3


def test_high_correctness_with_verified_error_lowers_confidence():
    e = ev(9, misconceptions=["always slower"], evidence=[{"kind": "incorrect", "point": "always slower", "quote": "slower than an inner join always"}])
    g = gr.ground(e, answers=[ANSWER], non_attempt=False)
    assert g.confidence == "medium" and any(f["code"] == "high_correctness_with_errors" for f in g.flags)


def test_high_score_without_any_evidence_lowers_confidence():
    g = gr.ground(ev(9, correct=[]), answers=[ANSWER], non_attempt=False)
    assert g.confidence == "medium"


@pytest.mark.parametrize("kw,expected", [
    (dict(score=9), "correct"),
    (dict(score=4, misconceptions=["always slower"], evidence=[{"kind": "incorrect", "point": "always slower", "quote": "slower than an inner join always"}]), "incorrect"),
    (dict(score=5), "partially_correct"),
    (dict(score=8, confidence="low"), "uncertain"),                       # ambiguous answer: the grader is unsure
    (dict(score=1, correct=[]), "no_attempt"),
])
def test_classification(kw, expected):
    assert gr.ground(ev(**kw), answers=[ANSWER], non_attempt=False).classification == expected


def test_correct_but_incomplete():
    e = LLMEvaluation.model_validate(graded(8, extra={"dimension_scores": {"correctness": 8, "completeness": 4, "depth": 5, "practical_application": 5,
                                                                            "clarity": 8, "production_awareness": 0}}))
    assert gr.ground(e, answers=[ANSWER], non_attempt=False).classification == "correct_incomplete"


def test_alternative_valid_approach_without_errors_is_correct():
    """A different but valid approach: the grader lists no misconceptions, so nothing can make it 'incorrect'."""
    e = ev(8, correct=["Uses NOT EXISTS instead of a LEFT JOIN anti-join, which is equivalent"], evidence=[])
    assert gr.ground(e, answers=["I would use NOT EXISTS with a correlated subquery"], non_attempt=False).classification == "correct"


def test_voice_answer_quotes_match_the_raw_or_repaired_text():
    e = ev(8, evidence=[{"kind": "correct", "point": "MySQL", "quote": "MySQL supports transactions"}])
    g = gr.ground(e, answers=["my sequel supports transactions", "MySQL supports transactions"], non_attempt=False)
    assert g.evidence[0].verified


def test_garbage_evidence_from_the_model_is_tolerated():
    e = LLMEvaluation.model_validate(graded(7, extra={"evidence": ["not a dict", {"kind": "weird", "quote": 5}, None]}))
    assert len(e.evidence) == 1 and e.evidence[0].kind == "correct"
