"""Evidence grounding and consistency checks for one evaluation. Pure functions, no model calls.

The model's analysis is useful but untrusted. This module checks it against the candidate's actual answer:

* every quote the grader cites must really occur in the answer (after normalising case, punctuation and spacing);
* a misconception counts as an error only if it is grounded (a verified "incorrect" quote supports it, or text it quotes is in
  the answer). Ungrounded ones are kept, clearly labelled as unverified, and never drive the classification;
* contradictions between the analysis and the scores are detected and resolved by small, documented, deterministic rules;
* the answer is classified (correct / correct but incomplete / partially correct / incorrect / no attempt / uncertain) so an
  incomplete explanation is never reported as a wrong one.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from ..schemas import DimensionScores, EvidenceItem, LLMEvaluation

_WORD = re.compile(r"[a-z0-9]+")
_QUOTED = re.compile(r"[\"“'‘]([^\"”'’]{6,200})[\"”'’]")


def _norm(text: str) -> str:
    return " ".join(_WORD.findall((text or "").lower()))


def quote_in_answer(quote: str, answers: list[str], min_words: int = 2) -> bool:
    """True when `quote` (normalised) occurs in one of the answers. Very short quotes prove nothing and are not accepted.
    A quote may elide words with "..." - each fragment must then appear, in order."""
    fragments = [f for f in (_norm(x) for x in re.split(r"\.\.\.|…", quote or "")) if f]
    if not fragments or sum(len(f.split()) for f in fragments) < min_words:
        return False
    for ans in answers:
        hay = f" {_norm(ans)} "
        pos, ok = 0, True
        for f in fragments:
            i = hay.find(f" {f} ", pos)
            if i < 0:
                ok = False
                break
            pos = i + len(f)
        if ok:
            return True
    return False


_STOP = {"the", "and", "that", "this", "candidate", "said", "says", "states", "stated", "claims", "claimed", "thinks", "believes", "answer",
         "with", "for", "are", "was", "were", "not", "which", "what", "from", "they", "their", "there", "into", "than", "then", "when",
         "always", "never", "only", "also", "about", "incorrectly", "wrongly", "mentions", "mentioned", "suggests", "implies"}


def _tokens(text: str) -> set[str]:
    return {t for t in _WORD.findall((text or "").lower()) if len(t) > 2 and t not in _STOP}


def _related(a: str, b: str, threshold: float = 0.4) -> bool:
    """Content-word overlap (boilerplate such as "the candidate said" removed) between a misconception and a quoted error."""
    x, y = _tokens(a), _tokens(b)
    return bool(x and y) and len(x & y) >= 1 and len(x & y) / min(len(x), len(y)) >= threshold


@dataclass
class Grounding:
    evidence: list[EvidenceItem]
    grounded_misconceptions: list[str]
    unverified_misconceptions: list[str]
    flags: list[dict[str, str]] = field(default_factory=list)
    adjustments: list[str] = field(default_factory=list)
    dimension_scores: Optional[DimensionScores] = None
    confidence: str = "medium"
    classification: str = "partially_correct"


def verify_evidence(ev: LLMEvaluation, answers: list[str]) -> list[EvidenceItem]:
    out = []
    for item in ev.evidence:
        if not item.quote and not item.point:
            continue
        out.append(item.model_copy(update={"verified": quote_in_answer(item.quote, answers)}))
    return out


def split_misconceptions(misconceptions: list[str], evidence: list[EvidenceItem], answers: list[str]) -> tuple[list[str], list[str]]:
    """(grounded, unverified). Grounded: an 'incorrect' quote that really is in the answer supports it, or text the
    misconception itself quotes is found in the answer. Single verified 'incorrect' quote with a single misconception also counts."""
    wrong_quotes = [e for e in evidence if e.kind == "incorrect" and e.verified]
    grounded, unverified = [], []
    for m in misconceptions:
        quoted = [q for q in _QUOTED.findall(m) if quote_in_answer(q, answers)]
        support = [e for e in wrong_quotes if _related(m, e.point + " " + e.quote)]
        if quoted or support or (len(misconceptions) == 1 and len(wrong_quotes) == 1):
            grounded.append(m)
        else:
            unverified.append(m)
    return grounded, unverified


def classify(*, dims: DimensionScores, grounded_misconceptions: list[str], correct_points: list[str], confidence: str,
             non_attempt: bool, claimed_errors: int = 0) -> str:
    """Deterministic answer classification. Errors must be grounded to call an answer incorrect."""
    if non_attempt:
        return "no_attempt"
    if confidence == "low":
        return "uncertain"
    c, comp = dims.correctness, dims.completeness
    if grounded_misconceptions and c <= 4:
        return "incorrect"
    if not grounded_misconceptions and not correct_points and c <= 2:
        # nothing right and nothing provably wrong: a claimed-but-unverified error means the grader may be mistaken
        if claimed_errors:
            return "uncertain"
        return "no_attempt" if comp <= 1 else "incorrect"
    if c >= 7 and comp >= 7 and not grounded_misconceptions:
        return "correct"
    if c >= 7 and not grounded_misconceptions:
        return "correct_incomplete"
    return "partially_correct"


CLASSIFICATION_LABELS = {
    "correct": "Correct", "correct_incomplete": "Correct but incomplete", "partially_correct": "Partially correct",
    "incorrect": "Incorrect", "no_attempt": "No real attempt", "uncertain": "Uncertain (grader unsure)",
}


def ground(ev: LLMEvaluation, *, answers: list[str], non_attempt: bool) -> Grounding:
    """Check one evaluation against the answer(s) it graded (for voice answers: raw transcript and repaired text)."""
    evidence = verify_evidence(ev, answers)
    grounded, unverified = split_misconceptions(ev.misconceptions, evidence, answers)
    dims = ev.dimension_scores.model_copy()
    flags: list[dict[str, str]] = []
    adjustments: list[str] = []
    confidence = ev.confidence

    unverified_quotes = [e for e in evidence if e.quote and not e.verified]
    if unverified_quotes:
        flags.append({"code": "unverified_quote", "message": f"{len(unverified_quotes)} quoted passage(s) cited by the grader were not found in the answer; they are shown as unverified."})
    if unverified:
        flags.append({"code": "ungrounded_misconception", "message": "Some claimed errors could not be tied to anything in the answer, so they are listed as unverified and not counted as mistakes."})

    # "I don't know"-style wording in a SHORT answer is only a non-attempt if the grader also saw nothing of value in it;
    # "You don't know the length upfront, so use a generator" is a real answer.
    non_attempt = non_attempt and (not ev.correct_points or dims.correctness <= 4)
    if non_attempt:
        high = [d for d in ("correctness", "completeness", "depth", "practical_application", "clarity") if getattr(dims, d) > 2]
        if high:
            for d in type(dims).model_fields:
                v = getattr(dims, d)
                if v is not None and v > 2:
                    setattr(dims, d, 2)
            adjustments.append("The answer was not a real attempt (e.g. \"I don't know\"), so every dimension was capped at 2.")
            flags.append({"code": "non_attempt_scored_high", "message": "The grader scored a non-attempt above 2; scores were capped."})
    else:
        if grounded and dims.correctness >= 8:
            flags.append({"code": "high_correctness_with_errors", "message": "Correctness was scored high although a verified error was found; confidence lowered."})
            confidence = "low" if confidence == "low" else "medium"
        # Requires >= 2 correct points and no claimed error at all (verified or not), so a forgotten misconception is not "corrected" away.
        if not grounded and not unverified and len(ev.correct_points) >= 2 and dims.correctness <= 3 and confidence != "low":
            # Nothing said was shown to be wrong: low marks belong under completeness, not correctness.
            adjustments.append(f"Correctness raised from {dims.correctness} to 5: no incorrect statement was identified, so the gaps are scored under completeness instead.")
            flags.append({"code": "incomplete_scored_as_incorrect", "message": "The answer was incomplete rather than wrong."})
            dims.correctness = 5
        if not ev.correct_points and dims.correctness >= 7 and not any(e.kind == "correct" and e.verified for e in evidence):
            flags.append({"code": "high_score_without_evidence", "message": "A high correctness score was given without citing anything correct; confidence lowered."})
            confidence = "low" if confidence == "low" else "medium"

    cls = classify(dims=dims, grounded_misconceptions=grounded, correct_points=ev.correct_points, confidence=confidence, non_attempt=non_attempt,
                   claimed_errors=len(unverified))
    return Grounding(evidence=evidence, grounded_misconceptions=grounded, unverified_misconceptions=unverified, flags=flags,
                     adjustments=adjustments, dimension_scores=dims, confidence=confidence, classification=cls)
