"""Answer evaluation: LLM call -> validation -> deterministic scoring and follow-up policy."""
from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic import BaseModel, ValidationError

from ..schemas import DimensionScores, Evaluation, LLMEvaluation, RubricSettings, _str_list
from . import eval_profiles, grounding
from .ollama import LLMError, OllamaClient
from .prompts import (PROMPT_VERSION, eval_schema_for, INTERPRET_SCHEMA, INTERPRET_SYSTEM, NARRATIVE_SCHEMA, NARRATIVE_SYSTEM, eval_system_prompt, eval_user_prompt,
                      interpret_user_prompt, FOLLOWUP_SCHEMA, FOLLOWUP_SYSTEM, followup_user_prompt,
                      repair_prompt, RESUME_SAFETY)

log = logging.getLogger("interviewer.evaluator")

VERDICTS = [(9.0, "Excellent"), (7.0, "Good"), (5.0, "Partial"), (3.0, "Weak"), (0.0, "Incorrect")]


def verdict_for(score: float) -> str:
    return next(label for floor, label in VERDICTS if score >= floor)


def drop_unclear(text: str, phrases: list[str], max_share: float = 0.3) -> str:
    """Remove phrases the model said it could not understand, so they are neither credited nor held against the speaker.

    Only exact (case-insensitive) matches of short phrases are removed, and never more than `max_share` of the text.
    """
    out, removed = text, 0
    for ph in phrases:
        if not ph or len(ph.split()) > 8:
            continue
        hit = re.search(re.escape(ph) + r"\s*[,;]?", out, re.I)   # take the comma that trailed the phrase with it
        if hit:
            removed += hit.end() - hit.start()
            out = out[: hit.start()] + out[hit.end():]
    if removed > len(text) * max_share:
        return text                                   # the model flagged too much: do not throw the answer away
    out = re.sub(r"\s+([,.;])", r"\1", re.sub(r"\s{2,}", " ", out))
    out = re.sub(r"([,;])\s*([,;.])", r"\2", out)   # ", ," left behind by a removed phrase
    return out.strip()


BASIC_DEPTH_FACTOR = 0.35   # a basic question (definition, simple difference) does not invite depth or real-world examples
DIFFICULTY_LEVEL = {"easy": "basic", "medium": "standard", "hard": "advanced"}


def question_level(model_level: str, difficulty: Optional[str]) -> str:
    """The difficulty the user set on the question wins; otherwise the model's classification."""
    return DIFFICULTY_LEVEL.get((difficulty or "").lower(), model_level or "standard")


def compute_score(dim: DimensionScores, production_relevant: bool, rubric: RubricSettings, level: str = "standard") -> float:
    """Weighted mean of the dimension scores (weights re-normalised; production only if relevant).

    For a *basic* question the depth and practical-application weights are scaled down, so a correct, clear, complete
    answer is not capped by dimensions the question never asked about.
    """
    f = BASIC_DEPTH_FACTOR if level == "basic" else 1.0
    parts = [
        (rubric.correctness, dim.correctness), (rubric.completeness, dim.completeness),
        (rubric.depth * f, dim.depth), (rubric.practical_application * f, dim.practical_application),
        (rubric.clarity, dim.clarity),
    ]
    if production_relevant:
        parts.append((rubric.production_awareness, dim.production_awareness))
    total_w = sum(w for w, _ in parts)
    if total_w <= 0:
        return round(sum(v for _, v in parts) / len(parts), 1)
    return round(sum(w * v for w, v in parts) / total_w, 1)


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 2}


def too_similar(candidate: str, previous: list[str], threshold: float = 0.7) -> bool:
    a = _tokens(candidate)
    if not a:
        return True
    for p in previous:
        b = _tokens(p)
        if b and len(a & b) / len(a | b) >= threshold:
            return True
    return False


_NON_ATTEMPT = re.compile(
    r"\b(i\s*)?(do\s*n[o']?t|don't|dont|cannot|can't|cant)\s+(really\s+)?(know|remember|recall|say)\b|\bno\s+(idea|clue)\b|"
    r"\bnot\s+(sure|certain)\b|\bi\s+have\s+no\s+(idea|experience)\b|^\s*(pass|skip|nothing|idk)\W*$", re.I)


def is_non_attempt(answer: str) -> bool:
    """A short 'I don't know'-style reply: there is nothing to build a follow-up on."""
    text = (answer or "").strip()
    return len(text.split()) <= 12 and bool(_NON_ATTEMPT.search(text))


@dataclass
class FollowUpDecision:
    ask: bool
    question: str = ""
    reason: str = ""
    suppressed_reason: Optional[str] = None


def decide_followup(ev: LLMEvaluation, *, max_followups: int, used_followups: int,
                    previous_questions: list[str], answer: str = "") -> FollowUpDecision:
    """Application-side policy. The prompt asks nicely; this function is what actually enforces limits."""
    if not ev.needs_followup or not ev.followup_question.strip():
        return FollowUpDecision(False, reason=ev.followup_reason)
    if max_followups <= 0:
        return FollowUpDecision(False, reason=ev.followup_reason, suppressed_reason="Follow-ups are disabled for this interview.")
    if used_followups >= max_followups:
        return FollowUpDecision(False, reason=ev.followup_reason,
                                suppressed_reason=f"Follow-up limit reached ({used_followups}/{max_followups}).")
    if is_non_attempt(answer):
        return FollowUpDecision(False, reason="No substantive attempt to build on, so further probing would not be useful.",
                                suppressed_reason="The answer was not a real attempt (e.g. \"I don't know\").")
    q = ev.followup_question.strip()
    if len(q) < 8:
        return FollowUpDecision(False, reason=ev.followup_reason, suppressed_reason="Follow-up was too short to be meaningful.")
    if too_similar(q, previous_questions):
        return FollowUpDecision(False, reason=ev.followup_reason, suppressed_reason="Follow-up repeated an earlier question.")
    return FollowUpDecision(True, question=q, reason=ev.followup_reason)


@dataclass
class EvalContext:
    question: str
    rubric: Optional[str]
    topic: Optional[str]
    difficulty: Optional[str]
    interview_type: str
    strictness: str
    current_question: str
    current_kind: str
    answer: str
    thread: list[dict[str, Any]] = field(default_factory=list)
    followups_remaining: int = 0
    answer_source: str = "typed"      # "voice": the text came from speech recognition and may contain misheard words
    claim: Optional[dict[str, Any]] = None   # resume questions only: {section, label, excerpt} of the claim being defended (untrusted)
    profile_key: str = "general"            # evaluation profile (eval_profiles.detect_category); decides extra dimensions and weights


class Narrative(BaseModel):
    overall_summary: str = ""
    strengths: list[str] = []
    knowledge_gaps: list[str] = []
    repeated_misconceptions: list[str] = []
    topics_to_revise: list[str] = []
    recommendations: list[str] = []

    def model_post_init(self, _ctx: Any) -> None:
        for name in ("strengths", "knowledge_gaps", "repeated_misconceptions", "topics_to_revise", "recommendations"):
            setattr(self, name, _str_list(getattr(self, name)))


def _extract_json(raw: str) -> Any:
    text = raw.strip()
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.S)
    if fence:
        text = fence.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


class Evaluator:
    def __init__(self, ollama: OllamaClient):
        self.ollama = ollama
        self.last_input_hash: Optional[str] = None

    def _call_validated(self, messages: list[dict[str, str]], schema: dict[str, Any], model_cls, max_tokens=None, purpose: str = "chat"):
        raw = self.ollama.chat_json(messages, schema, max_tokens=max_tokens, purpose=purpose)
        try:
            return model_cls.model_validate(_extract_json(raw))
        except (json.JSONDecodeError, ValidationError, ValueError) as first:
            log.warning("model output failed validation (%s); one repair attempt", type(first).__name__)
            retry = messages + [{"role": "assistant", "content": raw[:4000]},
                                {"role": "user", "content": repair_prompt(str(first))}]
            raw2 = self.ollama.chat_json(retry, schema, max_tokens=max_tokens, purpose=purpose)
            try:
                return model_cls.model_validate(_extract_json(raw2))
            except (json.JSONDecodeError, ValidationError, ValueError) as second:
                raise LLMError("bad_response", "The model's reply could not be understood twice in a row. "
                                               "Your answer is saved; use Retry.") from second

    def call_json(self, messages: list[dict[str, str]], schema: dict[str, Any], model_cls, *, max_tokens: Optional[int] = None, purpose: str = "chat"):
        """A schema-validated model call with one repair attempt (same policy as grading). Raises LLMError when it fails twice."""
        return self._call_validated(messages, schema, model_cls, max_tokens=max_tokens, purpose=purpose)

    def interpret_transcript(self, question: str, transcript: str) -> str:
        """Repair speech-recognition errors before grading. Falls back to the original text on any problem, so grading never fails here."""
        messages = [{"role": "system", "content": INTERPRET_SYSTEM}, {"role": "user", "content": interpret_user_prompt(question, transcript)}]
        try:
            data = _extract_json(self.ollama.chat_json(messages, INTERPRET_SCHEMA, max_tokens=500, purpose="repair"))
            text = str(data.get("text", "")).strip()
            unclear = [str(u).strip() for u in (data.get("unclear") or []) if str(u).strip()]
        except (LLMError, ValueError, AttributeError, TypeError):
            return transcript
        # a repair keeps the speaker's length; a much longer result means the model started answering for them
        if not text or len(text) > len(transcript) * 1.4 + 60:
            return transcript
        return drop_unclear(text, unclear)

    def evaluate(self, ctx: EvalContext, rubric: RubricSettings) -> LLMEvaluation:
        profile = eval_profiles.get_profile(ctx.profile_key)
        messages = [
            {"role": "system", "content": eval_system_prompt(ctx.interview_type, ctx.strictness, rubric, resume=bool(ctx.claim),
                                                             profile_block=eval_profiles.profile_prompt_block(profile))},
            {"role": "user", "content": eval_user_prompt(
                question=ctx.question, rubric=ctx.rubric, topic=ctx.topic, difficulty=ctx.difficulty,
                thread=ctx.thread, current_question=ctx.current_question, current_kind=ctx.current_kind,
                answer=ctx.answer, followups_remaining=ctx.followups_remaining, answer_source=ctx.answer_source, claim=ctx.claim)},
        ]
        raw = self._call_validated(messages, eval_schema_for(profile.extra_dimensions), LLMEvaluation, purpose="evaluation")
        raw.graded_by = self._route()                    # the app records which engine and model graded this; the model's own claim is ignored
        # reproducibility: the exact input that produced this grade can be identified later (the hash, never the text, is stored)
        self.last_input_hash = hashlib.sha256(json.dumps(messages, sort_keys=True).encode()).hexdigest()[:16]
        return raw

    def generation_settings(self) -> dict[str, Any]:
        settings = getattr(getattr(self.ollama, "local", self.ollama), "settings", None) or getattr(self.ollama, "settings", None)
        return {"temperature": getattr(settings, "llm_temperature", None)}

    def _route(self) -> Optional[dict[str, Any]]:
        getter = getattr(self.ollama, "last_route", None)
        return getter() if callable(getter) else None

    def writes_followups_separately(self) -> bool:
        """In cloud mode a dedicated conversation model writes the follow-up question; locally the grader's own question is used."""
        check = getattr(self.ollama, "is_cloud", None)
        return bool(check() if callable(check) else False)

    def generate_followup(self, *, question: str, answer: str, gap: str, draft: str, earlier: list[str], claim: Optional[dict[str, Any]] = None) -> Optional[str]:
        """One extra, optional model call. Any problem simply returns None and the grader's own draft is used."""
        system = FOLLOWUP_SYSTEM + (RESUME_SAFETY if claim else "")
        messages = [{"role": "system", "content": system}, {"role": "user", "content": followup_user_prompt(question=question, answer=answer, gap=gap, draft=draft, earlier=earlier, claim=claim)}]
        try:
            data = _extract_json(self.ollama.chat_json(messages, FOLLOWUP_SCHEMA, max_tokens=300, purpose="followup"))
            text = str(data.get("question", "")).strip()
        except (LLMError, ValueError, AttributeError, TypeError):
            return None
        if not 12 <= len(text) <= 400 or too_similar(text, [question, *earlier]):
            return None
        return text

    def finalize(self, raw: LLMEvaluation, rubric: RubricSettings, decision: FollowUpDecision,
                 difficulty: Optional[str] = None, interpreted_answer: Optional[str] = None, *,
                 answer: Optional[str] = None, profile_key: str = "general", input_hash: Optional[str] = None,
                 followup_kind: Optional[str] = None) -> Evaluation:
        """Validated model analysis -> grounded, deterministically scored evaluation. The model never supplies the total."""
        g = self.assess(raw, answer=answer, interpreted_answer=interpreted_answer)
        level = question_level(raw.question_level, difficulty)
        profile = eval_profiles.get_profile(profile_key)
        result = eval_profiles.score_answer(g.dimension_scores, profile, rubric, level, raw.production_relevant)
        data = raw.model_dump()
        data["dimension_scores"] = g.dimension_scores.model_dump()
        data["misconceptions"] = g.grounded_misconceptions if answer is not None else raw.misconceptions
        data["evidence"] = [e.model_dump() for e in g.evidence]
        data["confidence"] = g.confidence
        data["question_level"] = level
        data["interpreted_answer"] = interpreted_answer
        data["followup_question"] = decision.question if decision.ask else ""
        data["needs_followup"] = decision.ask
        data["followup_reason"] = decision.reason or raw.followup_reason
        flags = list(g.flags)
        if result.missing_dimensions:
            flags.append({"code": "dimension_not_scored", "message": "Not scored by the grader and left out of the weighting: " + ", ".join(result.missing_dimensions) + "."})
        provenance = {"prompt_version": PROMPT_VERSION, "profiles_version": eval_profiles.PROFILES_VERSION,
                      "rubric": eval_profiles.rubric_fingerprint(profile, rubric), "level": level,
                      "graded_by": raw.graded_by, "input_hash": input_hash, **self.generation_settings()}
        return Evaluation(**data, score=result.score, verdict=verdict_for(result.score), followup_asked=decision.ask,
                          followup_suppressed_reason=decision.suppressed_reason, profile=profile.key, profile_label=profile.label,
                          weights=result.weights, classification=g.classification,
                          unverified_misconceptions=g.unverified_misconceptions if answer is not None else [],
                          consistency_flags=flags, adjustments=g.adjustments, followup_kind=followup_kind if decision.ask else None,
                          provenance=provenance)

    @staticmethod
    def assess(raw: LLMEvaluation, *, answer: Optional[str], interpreted_answer: Optional[str] = None) -> grounding.Grounding:
        """Grounding + consistency checks. Without the answer text (legacy callers) the model's analysis is taken as given."""
        if answer is None:
            return grounding.Grounding(evidence=list(raw.evidence), grounded_misconceptions=list(raw.misconceptions), unverified_misconceptions=[],
                                       dimension_scores=raw.dimension_scores.model_copy(), confidence=raw.confidence,
                                       classification=grounding.classify(dims=raw.dimension_scores, grounded_misconceptions=raw.misconceptions,
                                                                         correct_points=raw.correct_points, confidence=raw.confidence, non_attempt=False))
        answers = [a for a in (answer, interpreted_answer) if a]
        return grounding.ground(raw, answers=answers, non_attempt=is_non_attempt(answer))

    def narrative(self, digest: str) -> Narrative:
        messages = [{"role": "system", "content": NARRATIVE_SYSTEM},
                    {"role": "user", "content": digest}]
        return self._call_validated(messages, NARRATIVE_SCHEMA, Narrative, max_tokens=900, purpose="summary")
