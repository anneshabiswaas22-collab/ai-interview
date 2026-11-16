"""Candidate profile: a structured, source-referenced understanding of one resume. Deterministic; no model calls.

Built from the user's saved (possibly corrected) profile plus the raw extracted text:

* every entry is checked against the raw text it supposedly came from (`verified` / `partial` / `not_found` + line number), so
  anything the AI organiser reworded or invented is visible instead of silently trusted;
* skills are merged across the skills section, projects and roles (aliases collapsed: "Postgres" = "PostgreSQL") with a confidence
  that reflects evidence of use, not just a listing;
* claims needing clarification (vague contributions, impact without a measure, numbers without a baseline, listed-only skills,
  roles without detail, gaps) are surfaced as topics worth exploring - never as accusations;
* text that looks like instructions aimed at an AI is flagged (it is always treated as data);
* claim-grounded interview questions are derived from the technical implications of what each claim names.

Corrections: the user edits the profile on the resume page; this module is recomputed from the saved profile on every request.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any, Optional

from ..schemas import ResumeProfile
from . import tech_implications as ti
from .evaluator import too_similar
from .resume_questions import METRIC_RE, parse_when

_W = re.compile(r"[a-z0-9]+")
VAGUE_RE = re.compile(r"^\s*(helped|assisted|involved in|worked on|participated|contributed to|responsible for|exposure to|familiar with|supported|part of)\b", re.I)
IMPACT_RE = re.compile(r"\b(improv|increas|reduc|decreas|optimi[sz]|boost|cut|sav|accelerat|grew|grow)\w*", re.I)
WE_RE = re.compile(r"\b(we|our team|the team)\b", re.I)
INJECTION_RE = re.compile(
    r"(ignore (all |any |the )?(previous|prior|above|earlier) (instructions|prompts?)|disregard (the|all|previous)|you are now|system prompt|"
    r"rate (this|the) (candidate|resume)|score (this|me|the candidate)|give (this|me) (a )?(10|full marks|perfect)|<\|im_start\|>|\[inst\]|### ?instruction|"
    r"as an ai( language model)?|assistant:|hire this candidate)", re.I)
CLAIM_EXCERPT = 400


def _norm(text: str) -> str:
    return " ".join(_W.findall((text or "").lower()))


def _clip(text: str, n: int) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


class SourceIndex:
    """Locates profile text in the raw extracted resume text."""

    def __init__(self, raw: str):
        self.lines = [_norm(x) for x in (raw or "").splitlines()]
        self.full = " " + " ".join(x for x in self.lines if x) + " "
        self.tokens = set(self.full.split())
        self.has_text = bool(self.full.strip())

    def locate(self, text: str) -> dict[str, Any]:
        n = _norm(text)
        if not n:
            return {"status": "not_found", "line": None}
        if not self.has_text:
            return {"status": "unknown", "line": None}
        words = n.split()
        if f" {n} " in self.full:
            status = "verified"
        else:
            covered = sum(1 for w in words if w in self.tokens) / len(words)
            status = "partial" if covered >= 0.8 else "not_found"
        probe = " ".join(words[:4])
        line = next((i + 1 for i, ln in enumerate(self.lines) if probe and probe in ln), None)
        if line is None and words:
            line = next((i + 1 for i, ln in enumerate(self.lines) if f" {words[0]} " in f" {ln} " and len(words[0]) > 3), None)
        return {"status": status, "line": line}


@dataclass
class Context:
    """A role or project: the unit a claim lives in."""
    key: str
    section: str          # Experience | Projects
    label: str
    head: str
    bullets: list[str]
    tech: list[str]


def _clean_lines(items: list[str]) -> list[str]:
    """Resume lines that look like instructions to an AI never reach a question, an excerpt or a prompt (they are still reported)."""
    return [x for x in items if not INJECTION_RE.search(x)]


def _contexts(p: ResumeProfile) -> list[Context]:
    out: list[Context] = []
    for i, e in enumerate(p.experience):
        role = " at ".join(x for x in (e.title, e.company) if x) or f"Role {i + 1}"
        if INJECTION_RE.search(role):
            continue
        dates = " – ".join(x for x in (e.start, "present" if e.is_current and not e.end else e.end) if x)
        out.append(Context(f"exp:{i}", "Experience", role, ", ".join(x for x in (role, e.location, dates) if x), _clean_lines(list(e.bullets)), []))
    for i, pr in enumerate(p.projects):
        name = pr.name or f"Project {i + 1}"
        if INJECTION_RE.search(name):
            continue
        out.append(Context(f"prj:{i}", "Projects", name, name + (f" ({pr.role})" if pr.role else ""), _clean_lines(list(pr.bullets)), _clean_lines(list(pr.tech))))
    return out


def _ctx_phrase(c: Context) -> str:
    return f"the {c.label} project" if c.section == "Projects" else f"your role as {c.label}"


# ---------------------------------------------------------------- skills
def skill_inventory(p: ResumeProfile, contexts: list[Context], src: SourceIndex) -> list[dict[str, Any]]:
    inv: dict[str, dict[str, Any]] = {}

    def entry(name: str, category: str) -> dict[str, Any]:
        canon, cat = ti.canonical(name)
        key = canon.lower()
        if key not in inv:
            inv[key] = {"name": canon, "category": cat or category or "Other", "listed": False, "used_in": [], "sources": [], "aliases": []}
        if name.strip() and name.strip() != canon and name.strip() not in inv[key]["aliases"]:
            inv[key]["aliases"].append(name.strip())
        return inv[key]

    for g in p.skills:
        for item in g.items:
            e = entry(item, g.group)
            e["listed"] = True
            loc = src.locate(item)
            e["sources"].append({"section": "Skills", "label": g.group or "Skills", "line": loc["line"], "status": loc["status"]})
    for c in contexts:
        text = " ".join([c.head, *c.bullets, *c.tech])
        names = {h.tech.name for h in ti.detect(text) if not h.activity} | set(c.tech)
        for name in names:
            e = entry(name, "")
            if c.label not in e["used_in"]:
                e["used_in"].append(c.label)
                e["sources"].append({"section": c.section, "label": c.label, "line": src.locate(c.head)["line"], "status": src.locate(c.head)["status"]})
    out = []
    for e in inv.values():
        if e["listed"] and e["used_in"]:
            conf, why = "high", f"Listed as a skill and used in {len(e['used_in'])} role/project(s)."
        elif e["used_in"]:
            conf, why = "medium", "Used in a role or project but not listed under skills."
        else:
            conf, why = "low", "Listed under skills only; no role or project shows it in use."
        out.append({**e, "evidence_count": len(e["used_in"]), "confidence": conf, "confidence_reason": why})
    out.sort(key=lambda e: ({"high": 0, "medium": 1, "low": 2}[e["confidence"]], -e["evidence_count"], e["name"].lower()))
    return out


# ---------------------------------------------------------------- experience
def _months(start: Optional[date], end: Optional[date]) -> int:
    if not start or not end or end < start:
        return 0
    return (end.year - start.year) * 12 + end.month - start.month + 1


def experience_summary(p: ResumeProfile, today: Optional[date] = None) -> dict[str, Any]:
    today = today or date.today()
    spans: list[tuple[date, date]] = []
    for e in p.experience:
        s = parse_when(e.start)
        end = today if (e.is_current or "present" in (e.end or "").lower() or "current" in (e.end or "").lower()) else parse_when(e.end)
        if s and end and end >= s:
            spans.append((s, end))
    spans.sort()
    merged: list[list[date]] = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    months = sum(_months(s, e) for s, e in merged)
    gaps = []
    for (_, a_end), (b_start, _) in zip(merged, merged[1:], strict=False):
        m = _months(a_end, b_start) - 2          # adjacent months are not a gap
        if m >= 6:
            gaps.append({"from": a_end.isoformat()[:7], "to": b_start.isoformat()[:7], "months": m})
    return {"roles": len(p.experience), "companies": sorted({e.company for e in p.experience if e.company}),
            "dated_roles": len(spans), "total_months": months, "years": round(months / 12, 1) if months else None, "gaps": gaps,
            "current": [" at ".join(x for x in (e.title, e.company) if x) for e in p.experience if e.is_current]}


# ---------------------------------------------------------------- relationships, projects, claims
def tech_relationships(contexts: list[Context], limit: int = 20) -> list[dict[str, Any]]:
    pairs: dict[tuple[str, str], list[str]] = {}
    for c in contexts:
        names = sorted({h.tech.name for h in ti.detect(" ".join([c.head, *c.bullets, *c.tech])) if not h.activity}
                       | {ti.canonical(t)[0] for t in c.tech})
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                pairs.setdefault((a, b), []).append(c.label)
    rows = [{"a": a, "b": b, "contexts": ctx, "strength": len(ctx)} for (a, b), ctx in pairs.items()]
    rows.sort(key=lambda r: (-r["strength"], r["a"], r["b"]))
    return rows[:limit]


def claims(contexts: list[Context], p: ResumeProfile, src: SourceIndex) -> list[dict[str, Any]]:
    """Responsibilities and achievements, each with its source reference."""
    out = []
    for c in contexts:
        for b in c.bullets:
            kind = "achievement" if (METRIC_RE.search(b) or IMPACT_RE.search(b)) else "responsibility"
            out.append({"kind": kind, "section": c.section, "label": c.label, "text": b, "has_metric": bool(METRIC_RE.search(b)), "source": src.locate(b)})
    for a in _clean_lines(list(p.achievements)):
        out.append({"kind": "achievement", "section": "Achievements", "label": "Achievements", "text": a, "has_metric": bool(METRIC_RE.search(a)), "source": src.locate(a)})
    return out


def clarification_areas(p: ResumeProfile, contexts: list[Context], skills: list[dict[str, Any]], exp: dict[str, Any]) -> list[dict[str, Any]]:
    """Statements worth exploring in an interview. Wording is neutral: unclear is not untrue."""
    out: list[dict[str, Any]] = []

    def add(kind: str, section: str, label: str, text: str, why: str, prompt: str) -> None:
        out.append({"kind": kind, "section": section, "label": label, "text": _clip(text, 300), "why": why, "suggested_question": prompt})

    for c in contexts:
        if c.section == "Experience" and not c.bullets:
            add("role_without_detail", c.section, c.label, c.head, "This role has no description of what you did.",
                f"What were your main responsibilities as {c.label}, and what are you proudest of there?")
        for b in c.bullets:
            metric = METRIC_RE.search(b)
            if VAGUE_RE.search(b):
                add("vague_contribution", c.section, c.label, b, "The wording does not say what you personally did.",
                    f"In {_ctx_phrase(c)}, which part of \"{_clip(b, 80)}\" did you do yourself?")
            elif WE_RE.search(b):
                add("team_vs_individual", c.section, c.label, b, "Describes team work; your own share is unclear.",
                    f"In {_ctx_phrase(c)}, what was your individual contribution to \"{_clip(b, 80)}\"?")
            if metric:
                add("metric_needs_context", c.section, c.label, b, f"A number ({metric.group(0).strip()}) without the baseline or how it was measured.",
                    f"How was the {metric.group(0).strip()} in {_ctx_phrase(c)} measured, and what was the baseline?")
            elif IMPACT_RE.search(b):
                add("unquantified_impact", c.section, c.label, b, "Claims an improvement without saying how much or how it was measured.",
                    f"How did you measure the improvement in \"{_clip(b, 80)}\"?")
    for s in skills:
        if s["confidence"] == "low":
            add("listed_skill_without_evidence", "Skills", s["name"], s["name"], "Listed as a skill, but no role or project shows it in use.",
                f"Where have you used {s['name']} in practice, and what did you build with it?")
    for g in exp["gaps"]:
        add("timeline_gap", "Experience", f"{g['from']} → {g['to']}", f"About {g['months']} months between roles",
            "A gap between roles; interviewers often ask about it.", "What did you focus on between those roles?")
    return out[:40]


def injection_warnings(raw: str) -> list[dict[str, Any]]:
    out = []
    for i, line in enumerate((raw or "").splitlines(), start=1):
        if INJECTION_RE.search(line):
            out.append({"line": i, "text": _clip(line, 160)})
    return out[:10]


def extraction_quality(p: ResumeProfile, src: SourceIndex) -> dict[str, Any]:
    """How much of the organised profile can be found in the raw text. Low numbers mean: check the profile for AI rewording."""
    checks = [b for e in p.experience for b in e.bullets] + [b for pr in p.projects for b in pr.bullets] + list(p.achievements)
    checks += [x for x in (*(e.company for e in p.experience), *(e.title for e in p.experience), *(pr.name for pr in p.projects)) if x]
    counts = {"verified": 0, "partial": 0, "not_found": 0, "unknown": 0}
    not_found = []
    for t in checks:
        st = src.locate(t)["status"]
        counts[st] += 1
        if st == "not_found":
            not_found.append(_clip(t, 120))
    total = len(checks)
    score = round((counts["verified"] + 0.6 * counts["partial"]) / total, 2) if total and src.has_text else None
    level = None if score is None else ("high" if score >= 0.85 else "medium" if score >= 0.6 else "low")
    return {"checked": total, **counts, "score": score, "confidence": level, "not_found_examples": not_found[:5]}


# ---------------------------------------------------------------- questions
PROJECT_STAGES: list[tuple[str, str, str, str]] = [
    ("problem", "easy", "What problem did {name} solve, who used it, and what did success look like?", "Clear problem statement, users, success criteria."),
    ("architecture", "medium", "Walk me through the architecture of {name}{tech_clause}: the main components and how data flows between them.", "Components, responsibilities, data flow, the candidate's own part."),
    ("decision", "medium", "Which technology or design decision in {name} would you defend most strongly, and what alternatives did you reject?", "Concrete alternatives, criteria, trade-offs."),
    ("testing", "medium", "How did you test {name}, and what kind of bug still got through?", "Test levels, what was automated, a real escaped defect and the fix."),
    ("failure", "hard", "What happens in {name} when a dependency fails or the input is bad, and how would you find out?", "Failure modes, retries/timeouts, validation, monitoring/alerting."),
    ("scale", "hard", "If usage of {name} grew tenfold, what would break first and what would you change?", "Identifies the bottleneck, concrete changes, cost awareness."),
    ("security", "medium", "How were secrets, access and user data protected in {name}?", "Secret management, authn/authz, least privilege, data protection."),
    ("future", "easy", "With what you know now, what would you redesign in {name}?", "Honest reflection, specific improvements, reasons."),
]


def suggested_questions(resume_id: int, resume_name: str, contexts: list[Context], areas: list[dict[str, Any]], *,
                        limit: int = 12, exclude: Optional[list[str]] = None) -> list[dict[str, Any]]:
    """Claim-grounded questions. Each carries the exact claim (section, label, excerpt) it is about, so it can be traced and graded
    as a resume question. Order interleaves sources (technology implications, project deep-dive, clarifications) for variety."""
    streams: list[list[dict[str, Any]]] = [[], [], []]
    seen_tech: set[tuple[str, str]] = set()
    for c in contexts:
        excerpt = _clip(c.head + (": " + " • ".join(c.bullets) if c.bullets else ""), CLAIM_EXCERPT)
        claim = {"section": c.section, "label": c.label, "excerpt": excerpt}
        text = " ".join([c.head, *c.bullets, *c.tech])
        for h in ti.detect(text):
            for q, diff, kind, rubric in h.tech.questions:
                if (h.tech.name, c.key) in seen_tech and kind in {x["kind"] for x in streams[0] if x["claim"]["label"] == c.label}:
                    continue
                streams[0].append(_q(resume_id, resume_name, q.format(ctx=_ctx_phrase(c)), rubric, h.tech.name, diff, kind, claim))
            seen_tech.add((h.tech.name, c.key))
        if c.section == "Projects":
            techs = [ti.canonical(t)[0] for t in c.tech][:3]
            clause = f" (built with {', '.join(techs)})" if techs else ""
            for stage, diff, tmpl, rubric in PROJECT_STAGES:
                streams[1].append(_q(resume_id, resume_name, tmpl.format(name=c.label, tech_clause=clause), rubric, "Project deep-dive", diff, f"project_{stage}", claim))
    for a in areas:
        if a["kind"] in ("timeline_gap",):
            continue
        claim = {"section": a["section"], "label": a["label"], "excerpt": _clip(a["text"], CLAIM_EXCERPT)}
        streams[2].append(_q(resume_id, resume_name, a["suggested_question"], "A specific, first-person account: their own actions, how results were measured, what they learned.",
                             "Resume clarification", "medium", a["kind"], claim))
    out: list[dict[str, Any]] = []
    taken = list(exclude or [])
    idx = [0, 0, 0]
    while len(out) < limit and any(idx[i] < len(streams[i]) for i in range(3)):
        for i in range(3):
            while idx[i] < len(streams[i]):
                q = streams[i][idx[i]]
                idx[i] += 1
                if not too_similar(q["text"], taken, threshold=0.6):
                    out.append(q)
                    taken.append(q["text"])
                    break
            if len(out) >= limit:
                break
    return out


def _q(rid: int, rname: str, text: str, rubric: str, topic: str, difficulty: str, kind: str, claim: dict[str, str]) -> dict[str, Any]:
    return {"text": text, "rubric": rubric, "topic": topic, "difficulty": difficulty, "kind": kind, "resume_id": rid, "resume_name": rname, "claim": claim}


def claim_inventory(profile: ResumeProfile) -> list[dict[str, str]]:
    """The roles and projects an interview could discuss (cheap: used for every interview plan)."""
    return [{"section": c.section, "label": c.label} for c in _contexts(profile)]


# ---------------------------------------------------------------- entry point
def build(resume_id: int, resume_name: str, profile: ResumeProfile, raw_text: str, *, today: Optional[date] = None,
          question_limit: int = 12, exclude: Optional[list[str]] = None) -> dict[str, Any]:
    src = SourceIndex(raw_text)
    contexts = _contexts(profile)
    skills = skill_inventory(profile, contexts, src)
    exp = experience_summary(profile, today)
    areas = clarification_areas(profile, contexts, skills, exp)
    projects = []
    for c in contexts:
        if c.section != "Projects":
            continue
        techs = sorted({h.tech.name for h in ti.detect(" ".join([c.head, *c.bullets])) if not h.activity} | {ti.canonical(t)[0] for t in c.tech})
        projects.append({"name": c.label, "tech": techs, "bullets": len(c.bullets), "has_metrics": any(METRIC_RE.search(b) for b in c.bullets),
                         "source": src.locate(c.label), "clarifications": sum(1 for a in areas if a["label"] == c.label)})
    return {
        "resume_id": resume_id, "resume_name": resume_name,
        "skills": skills, "projects": projects, "experience": exp, "relationships": tech_relationships(contexts),
        "claims": claims(contexts, profile, src), "clarifications": areas,
        "extraction": extraction_quality(profile, src), "injection_warnings": injection_warnings(raw_text),
        "suggested_questions": suggested_questions(resume_id, resume_name, contexts, areas, limit=question_limit, exclude=exclude),
        "claim_inventory": claim_inventory(profile),
        "notes": ["Built from your saved profile; edit the profile to correct anything and this view updates.",
                  "Clarification areas are things an interviewer may ask about, not judgements about honesty."],
    }
