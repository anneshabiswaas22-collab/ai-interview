"""Evaluation profiles: which dimensions apply to a question, how they are weighted and what each score means.

A profile is chosen by deterministic rules from the interview type, the question's topic and its text (never by the model).
The final score is computed here from the validated dimension scores; the model never supplies a total.

Versioning: every profile carries a version, and `rubric_fingerprint` hashes the exact weights that were applied, so a
stored evaluation says precisely which rubric produced its score (see `Evaluation.provenance`).
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Optional

from ..schemas import DimensionScores, RubricSettings

PROFILES_VERSION = 2          # bump when any profile's weights, dimensions or descriptors change

# ---------------------------------------------------------------- dimension catalogue
# The five core dimensions are always scored (they are part of the validated contract since v1). Extra dimensions are requested
# only by the profiles that need them, and are optional in the contract: a missing one is excluded from the weighting, never zero.
CORE_DIMENSIONS = ("correctness", "completeness", "depth", "practical_application", "clarity")
EXTRA_DIMENSIONS = ("conceptual_understanding", "problem_solving", "edge_cases", "tradeoffs")
ALL_DIMENSIONS = CORE_DIMENSIONS + ("production_awareness",) + EXTRA_DIMENSIONS
LEGACY_DIMENSIONS = CORE_DIMENSIONS + ("production_awareness",)     # the ones the user's rubric editor controls

DIMENSION_LABELS = {
    "correctness": "Technical correctness", "completeness": "Completeness", "depth": "Depth of explanation",
    "practical_application": "Practical application", "clarity": "Communication clarity", "production_awareness": "Production awareness",
    "conceptual_understanding": "Conceptual understanding", "problem_solving": "Problem-solving", "edge_cases": "Edge-case awareness",
    "tradeoffs": "Trade-off analysis",
}
# What each dimension measures (shown to the model and printed in reports).
DIMENSION_MEANING = {
    "correctness": "is what was said true?",
    "completeness": "are the essential concepts covered for this question and its difficulty?",
    "depth": "understanding of why/how, not just what",
    "practical_application": "concrete usage, examples, real-world judgement",
    "clarity": "structure and reasoning of the explanation",
    "production_awareness": "monitoring, failures, scale, cost, safety",
    "conceptual_understanding": "grasp of the underlying model or theory (e.g. set semantics, the GIL, bias-variance)",
    "problem_solving": "a systematic approach: breaking the problem down, choosing and justifying a method",
    "edge_cases": "NULLs, empty inputs, duplicates, concurrency, limits, failure modes relevant to the question",
    "tradeoffs": "names alternatives and weighs their costs and benefits",
}
# Anchors for the extra dimensions (core anchors are in the base prompt). Short on purpose: small local models have little context.
EXTRA_ANCHORS = {
    "conceptual_understanding": "0-3 confuses the concept; 4-6 knows the idea but not why; 7-8 explains the mechanism; 9-10 precise mental model.",
    "problem_solving": "0-3 no approach; 4-6 an approach without justification; 7-8 a sound, justified approach; 9-10 systematic and efficient.",
    "edge_cases": "0-3 none considered; 4-6 one obvious case; 7-8 the important cases; 9-10 thorough and prioritised.",
    "tradeoffs": "0-3 one option only; 4-6 alternatives named, not weighed; 7-8 weighed with reasons; 9-10 nuanced, context-dependent judgement.",
}
# Behavioural answers reuse the core dimensions with a different meaning.
BEHAVIOURAL_MEANING = {
    "correctness": "relevance and credibility of the example",
    "completeness": "situation, task, action and result are all present",
    "depth": "self-reflection: what they learned or would change",
    "practical_application": "a specific, concrete example rather than a generality",
    "clarity": "a structured, easy-to-follow story",
}


@dataclass(frozen=True)
class EvalProfile:
    key: str
    label: str
    version: int
    weights: dict[str, float]                       # relative; re-normalised over the dimensions actually scored
    basic_scaled: tuple[str, ...] = ("depth", "practical_application", "edge_cases", "tradeoffs")       # count less on basic questions (v1 rule)
    advanced_scaled: tuple[str, ...] = ("depth", "edge_cases", "tradeoffs", "production_awareness")    # count more on advanced questions
    meaning: dict[str, str] = field(default_factory=dict)   # profile-specific meaning of a dimension (behavioural)
    guidance: str = ""                              # one line added to the grading prompt

    @property
    def extra_dimensions(self) -> list[str]:
        return [d for d in EXTRA_DIMENSIONS if self.weights.get(d, 0) > 0]

    def meaning_of(self, dim: str) -> str:
        return self.meaning.get(dim) or DIMENSION_MEANING[dim]


def _p(key, label, guidance="", meaning=None, advanced_scaled=None, **w) -> EvalProfile:
    extra = {} if advanced_scaled is None else {"advanced_scaled": advanced_scaled}
    return EvalProfile(key=key, label=label, version=PROFILES_VERSION, weights=w, meaning=meaning or {}, guidance=guidance, **extra)


PROFILES: dict[str, EvalProfile] = {p.key: p for p in [
    # identical to the v1 global rubric, so questions without a recognisable category are scored exactly as before
    _p("general", "General technical", advanced_scaled=(), correctness=0.30, completeness=0.20, depth=0.15, practical_application=0.15, clarity=0.10, production_awareness=0.10),
    _p("sql", "SQL", "SQL: check set semantics, NULL handling, join/aggregation correctness and whether the query would return the right rows.",
       correctness=0.30, completeness=0.15, conceptual_understanding=0.10, problem_solving=0.10, edge_cases=0.10, depth=0.05,
       practical_application=0.10, clarity=0.05, production_awareness=0.05),
    _p("python", "Python", "Python: check language semantics (mutability, scoping, iteration, typing), idiomatic usage and error handling.",
       correctness=0.30, completeness=0.15, conceptual_understanding=0.10, problem_solving=0.10, edge_cases=0.10, depth=0.05,
       practical_application=0.10, clarity=0.10),
    _p("data_engineering", "Data engineering", "Data engineering: weigh idempotency, incremental loads, late or duplicate data, orchestration, data quality and cost.",
       correctness=0.25, completeness=0.15, depth=0.10, practical_application=0.10, problem_solving=0.05, edge_cases=0.10, tradeoffs=0.10,
       clarity=0.05, production_awareness=0.10),
    _p("machine_learning", "Machine learning", "ML: check the underlying statistics and modelling assumptions, evaluation methodology, leakage and generalisation.",
       correctness=0.25, completeness=0.15, conceptual_understanding=0.15, depth=0.10, practical_application=0.10, tradeoffs=0.10,
       clarity=0.05, production_awareness=0.10),
    _p("system_design", "System design", "System design: reward clear requirements, a justified architecture, data flow, scaling, failure handling and explicit trade-offs.",
       correctness=0.15, completeness=0.15, problem_solving=0.15, tradeoffs=0.20, depth=0.10, edge_cases=0.05, clarity=0.10,
       production_awareness=0.10),
    _p("software_engineering", "Software engineering", "Software engineering: weigh design principles, testing, maintainability and practical judgement.",
       correctness=0.25, completeness=0.15, depth=0.10, practical_application=0.15, problem_solving=0.10, tradeoffs=0.10, clarity=0.10,
       production_awareness=0.05),
    _p("behavioral", "Behavioural", "Behavioural: 'correctness' means relevance and credibility; reward specific, honest, structured (STAR) examples and reflection.",
       BEHAVIOURAL_MEANING, correctness=0.25, completeness=0.20, depth=0.15, practical_application=0.20, clarity=0.20),
]}

# ---------------------------------------------------------------- deterministic category detection
_RULES: list[tuple[str, re.Pattern]] = [
    ("behavioral", re.compile(r"\b(tell me about a time|describe a (time|situation)|conflict|disagree|feedback you|weakness|strength|motivat|teammate|stakeholder|leadership|behaviou?ral|hr)\b", re.I)),
    ("system_design", re.compile(r"\b(system design|design (a|an|the)\b|architect|scal(e|ability|ing)|load balanc|sharding|rate limit|high availability|microservice|cap theorem|distributed system)", re.I)),
    ("sql", re.compile(r"\b(sql|select|join|group by|having|window function|cte|index(es|ing)?|primary key|foreign key|normali[sz]|postgres|mysql|sqlite|query|queries|database)\b", re.I)),
    ("data_engineering", re.compile(r"\b(etl|elt|pipeline|airflow|dag|spark|kafka|streaming|batch|data warehouse|snowflake|bigquery|redshift|dbt|data lake|lakehouse|partition|cdc|incremental load|idempoten|data engineering|hadoop|flink)\b", re.I)),
    ("machine_learning", re.compile(r"\b(machine learning|ml\b|model training|overfit|underfit|regulari[sz]|gradient|neural|deep learning|classifier|regression|precision|recall|f1|bias.variance|feature engineering|feature scaling|cross.validation|llm|transformers?|embeddings?|batch normali[sz]ation|gradient descent)", re.I)),
    ("python", re.compile(r"\b(python|pythonic|list comprehension|generator|decorator|gil|asyncio|pandas|numpy|django|flask|fastapi|pip|virtualenv|__init__|dict(ionary)?|tuple)\b", re.I)),
    ("software_engineering", re.compile(r"\b(oop|object.oriented|solid|design pattern|unit test|testing|refactor|code review|ci/?cd|git|api|rest|concurren|thread|memory leak|complexity|algorithm|data structure|software engineering)\b", re.I)),
]
_TOPIC_ALIASES = {
    "sql": "sql", "database": "sql", "databases": "sql", "python": "python", "ml": "machine_learning", "machine learning": "machine_learning",
    "ai": "machine_learning", "data engineering": "data_engineering", "etl": "data_engineering", "system design": "system_design",
    "behavioral": "behavioral", "behavioural": "behavioral", "hr": "behavioral", "software engineering": "software_engineering",
}


def _hits(rx: re.Pattern, text: str) -> int:
    return len({m.group(0).lower() for m in rx.finditer(text)})


def detect_category(*, topic: Optional[str], text: str, interview_type: str = "technical") -> str:
    """Pick the profile for a question. Order: HR interview -> explicit topic alias -> topic keywords -> question keywords -> general.

    Within the topic (then the text), every rule is scored by its number of DISTINCT keyword hits; the best one wins only if it is
    unambiguous. A tie (e.g. "join a list of strings in Python": one SQL word, one Python word) falls back to the general profile,
    because a wrong profile is worse than a neutral one."""
    if interview_type == "hr":
        return "behavioral"
    t = (topic or "").strip().lower()
    if t in _TOPIC_ALIASES:
        return _TOPIC_ALIASES[t]
    for source, is_text in ((t, False), (text or "", True)):
        if not source:
            continue
        scores = {}
        for key, rx in _RULES:
            if key == "behavioral" and interview_type == "technical" and is_text:
                continue            # in a technical interview a passing "strength" in the question is not a behavioural question
            n = _hits(rx, source)
            if n:
                scores[key] = n
        if scores:
            best = max(scores.values())
            winners = [k for k, v in scores.items() if v == best]
            return winners[0] if len(winners) == 1 else "general"
    return "general"


def get_profile(key: str) -> EvalProfile:
    return PROFILES.get(key) or PROFILES["general"]


# ---------------------------------------------------------------- scoring
BASIC_FACTOR = 0.35            # basic questions: dimensions the question never asked about count much less
ADVANCED_FACTOR = 1.25         # advanced questions: depth, trade-offs, edge cases and production count a little more
_DEFAULT_RUBRIC = RubricSettings()


def effective_weights(profile: EvalProfile, rubric: RubricSettings, level: str, production_relevant: bool) -> dict[str, float]:
    """Profile weights x the user's rubric emphasis x the question level. Pure and deterministic.

    The user's rubric editor keeps its meaning: each legacy dimension is scaled by (user weight / default weight), so doubling
    "correctness" in Settings doubles it in every profile, and setting a weight to 0 removes that dimension everywhere.
    """
    out: dict[str, float] = {}
    for dim, w in profile.weights.items():
        if w <= 0:
            continue
        if dim == "production_awareness" and not production_relevant:
            continue
        if dim in LEGACY_DIMENSIONS:
            default = getattr(_DEFAULT_RUBRIC, dim)
            w *= (getattr(rubric, dim) / default) if default else 1.0
        if level == "basic" and dim in profile.basic_scaled:
            w *= BASIC_FACTOR
        elif level == "advanced" and dim in profile.advanced_scaled:
            w *= ADVANCED_FACTOR
        if w > 0:
            out[dim] = w
    return out


@dataclass
class ScoreResult:
    score: float
    weights: dict[str, float]          # normalised weights actually applied (sum to 1), for the report
    missing_dimensions: list[str]      # requested by the profile but not scored by the model (excluded, not zero)


def score_answer(dims: DimensionScores, profile: EvalProfile, rubric: RubricSettings, level: str, production_relevant: bool) -> ScoreResult:
    weights = effective_weights(profile, rubric, level, production_relevant)
    used: dict[str, float] = {}
    missing: list[str] = []
    for dim, w in weights.items():
        value = getattr(dims, dim, None)
        if value is None:
            missing.append(dim)
            continue
        used[dim] = w
    total = sum(used.values())
    if total <= 0:          # every weight zero: plain mean of the core dimensions
        vals = [getattr(dims, d) for d in CORE_DIMENSIONS]
        return ScoreResult(round(sum(vals) / len(vals), 1), {}, missing)
    score = sum(w * getattr(dims, d) for d, w in used.items()) / total
    return ScoreResult(round(score, 1), {d: round(w / total, 3) for d, w in used.items()}, missing)


def rubric_fingerprint(profile: EvalProfile, rubric: RubricSettings) -> str:
    """A short, stable id of the exact rubric that graded an answer: profile + version + the user's weights and guidance."""
    payload = json.dumps({"p": profile.key, "v": profile.version, "w": profile.weights,
                          "u": rubric.model_dump()}, sort_keys=True)
    return f"{profile.key}-v{profile.version}-{hashlib.sha256(payload.encode()).hexdigest()[:10]}"


def profile_prompt_block(profile: EvalProfile) -> str:
    """The profile-specific part of the grading prompt: its guidance, re-defined dimensions and any extra dimensions with anchors."""
    lines = [f"EVALUATION PROFILE: {profile.label}."]
    if profile.guidance:
        lines.append(profile.guidance)
    for dim, meaning in profile.meaning.items():
        lines.append(f"- In this profile {dim} means: {meaning}.")
    extra = profile.extra_dimensions
    if extra:
        lines.append("Also score these dimensions (0-10 integers) in dimension_scores:")
        for d in extra:
            lines.append(f"- {d}: {DIMENSION_MEANING[d]}. {EXTRA_ANCHORS[d]}")
    return "\n".join(lines)


def describe_profiles() -> list[dict]:
    """Public, read-only description of every profile (Settings page and docs)."""
    return [{"key": p.key, "label": p.label, "version": p.version, "guidance": p.guidance,
             "dimensions": [{"key": d, "label": DIMENSION_LABELS[d], "meaning": p.meaning_of(d), "weight": w}
                            for d, w in sorted(p.weights.items(), key=lambda kv: -kv[1]) if w > 0]}
            for p in PROFILES.values()]
