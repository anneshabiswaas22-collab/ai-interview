"""Report aggregation (deterministic), persistence and Markdown rendering.

Scoring rules (also printed in every report):
  * Question score = weighted mean of the evaluated answers on that question: the original answer counts 2,
    each follow-up answer counts 1. Rounded to 1 decimal.
  * Skipped questions and questions never reached are NOT scored: they are counted separately and are
    excluded from every average.
  * Answers that could not be evaluated (model error) are counted as 'answered, not scored' and excluded
    from averages.
  * Average score = mean of the question scores of scored questions. Topic average = mean of those within a topic.
"""
from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter
from typing import Any, Optional

from ..db import Database, utcnow
from ..errors import not_found
from .evaluator import verdict_for

MAIN_WEIGHT, FOLLOWUP_WEIGHT = 2, 1
SCORING_RULES = [
    "Question score = weighted mean of its evaluated answers (original answer weight 2, each follow-up weight 1).",
    "Skipped and unanswered questions are never scored as zero; they are counted separately and excluded from all averages.",
    "Answers that could not be evaluated are counted as answered but excluded from averages.",
    "Basic questions (a definition or simple difference) are judged mainly on correctness, completeness and clarity; depth and real-world examples count less. A difficulty you set on a question overrides the model's guess.",
    "Average score = mean of the scored question scores. Topic scores use the same rule within each topic.",
]
UNCATEGORIZED = "Uncategorized"


def item_score(turns: list[dict]) -> Optional[float]:
    num = den = 0.0
    for t in turns:
        if t["status"] == "evaluated" and t["score"] is not None:
            w = MAIN_WEIGHT if t["kind"] == "main" else FOLLOWUP_WEIGHT
            num += w * t["score"]
            den += w
    return round(num / den, 1) if den else None


def _tok(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 2}


def _cluster(entries: list[tuple[str, int]], threshold: float = 0.5) -> list[dict[str, Any]]:
    """Group near-identical statements coming from *different* questions."""
    clusters: list[dict[str, Any]] = []
    for text, pos in entries:
        a = _tok(text)
        for cl in clusters:
            b = cl["tokens"]
            if a and b and len(a & b) / len(a | b) >= threshold:
                cl["questions"].add(pos)
                cl["tokens"] = b | a
                break
        else:
            clusters.append({"text": text, "tokens": a, "questions": {pos}})
    return clusters


SKILLS = [("correctness", "Technical correctness"), ("completeness", "Completeness"), ("depth", "Depth of understanding"),
          ("practical_application", "Practical application"), ("clarity", "Clarity & reasoning"), ("production_awareness", "Production awareness"),
          ("conceptual_understanding", "Conceptual understanding"), ("problem_solving", "Problem-solving"), ("edge_cases", "Edge-case awareness"),
          ("tradeoffs", "Trade-off analysis")]


def skill_averages(turns_by_question: list[list[dict]]) -> list[dict[str, Any]]:
    """Average of each dimension over every evaluated answer (main answers and follow-ups). Production awareness counts only where it applied."""
    sums: dict[str, list[float]] = {k: [] for k, _ in SKILLS}
    for ts in turns_by_question:
        for t in ts:
            ev = t.get("evaluation")
            if not ev or t.get("status") != "evaluated":
                continue
            dims = ev.get("dimension_scores") or {}
            for key, _ in SKILLS:
                if key not in dims or dims[key] is None:
                    continue
                if key == "production_awareness" and not ev.get("production_relevant"):
                    continue
                sums[key].append(float(dims[key]))
    core = {"correctness", "completeness", "depth", "practical_application", "clarity", "production_awareness"}
    # the six v1 skills are always listed (stable shape); profile-specific ones only when at least one answer was scored on them
    return [{"key": k, "label": label, "average": round(sum(v) / len(v), 1) if v else None, "answers": len(v)}
            for (k, label), v in zip(SKILLS, sums.values(), strict=False) if k in core or v]


def build_report(c: sqlite3.Connection, iid: int) -> dict[str, Any]:
    iv = c.execute("SELECT * FROM interviews WHERE id=?", (iid,)).fetchone()
    items = [dict(r) for r in c.execute("SELECT * FROM interview_items WHERE interview_id=? ORDER BY position", (iid,))]
    turns = [dict(r) for r in c.execute("SELECT * FROM turns WHERE interview_id=? ORDER BY item_id, seq", (iid,))]
    by_item: dict[int, list[dict]] = {}
    for t in turns:
        by_item.setdefault(t["item_id"], []).append(t)

    questions = []
    for it in items:
        ts = by_item.get(it["id"], [])
        score = item_score(ts)
        tviews = []
        for t in ts:
            if t["status"] == "asked" and t["kind"] == "main" and it["status"] == "unanswered":
                continue
            tviews.append({
                "seq": t["seq"], "kind": t["kind"], "question": t["question_text"], "answer": t["answer_text"],
                "source": t["answer_source"], "status": t["status"], "score": t["score"],
                "followup_reason": t["followup_reason"],
                "evaluation": json.loads(t["evaluation_json"]) if t["evaluation_json"] else None,
            })
        q = {
            "position": it["position"] + 1, "text": it["text"], "topic": it["topic"], "difficulty": it["difficulty"],
            "status": it["status"], "score": score, "verdict": verdict_for(score) if score is not None else None,
            "followups_asked": it["followup_count"], "turns": tviews, "source": it.get("source") or "bank",
        }
        if q["source"] == "resume":
            q["resume_id"], q["resume_name"] = it.get("resume_id"), it.get("resume_name")
            q["claim"] = _load_claim(it.get("claim_json"))
        questions.append(q)

    scored = [q for q in questions if q["score"] is not None]
    unevaluated = sum(1 for q in questions if q["status"] == "answered" and q["score"] is None)
    summary = {
        "total_questions": len(items),
        "answered": sum(1 for q in questions if q["status"] == "answered"),
        "skipped": sum(1 for q in questions if q["status"] == "skipped"),
        "unanswered": sum(1 for q in questions if q["status"] == "unanswered"),
        "scored": len(scored), "answered_not_scored": unevaluated,
        "average_score": round(sum(q["score"] for q in scored) / len(scored), 1) if scored else None,
        "followups_asked": sum(q["followups_asked"] for q in questions),
    }
    summary["verdict"] = verdict_for(summary["average_score"]) if summary["average_score"] is not None else None

    topics: dict[str, list[dict]] = {}
    for q in questions:
        topics.setdefault(q["topic"] or UNCATEGORIZED, []).append(q)
    topic_rows = []
    for name, qs in topics.items():
        sc = [q["score"] for q in qs if q["score"] is not None]
        topic_rows.append({"topic": name, "questions": len(qs), "scored": len(sc),
                           "average_score": round(sum(sc) / len(sc), 1) if sc else None,
                           "question_numbers": [q["position"] for q in qs]})
    topic_rows.sort(key=lambda t: (t["average_score"] is None, t["average_score"] if t["average_score"] is not None else 0))

    out = {
        "interview": {"id": iv["id"], "title": iv["title"], "type": iv["interview_type"], "status": iv["status"],
                      "created_at": iv["created_at"], "completed_at": iv["completed_at"],
                      "config": json.loads(iv["config_json"])},
        "summary": summary, "topics": topic_rows, "questions": questions, "scoring_rules": SCORING_RULES,
        "skills": skill_averages([q["turns"] for q in questions]),
        "aggregated": rule_based_insights(questions, topic_rows, summary),
        "narrative": None,
    }
    claims = resume_claims(questions)
    if claims or any(q["source"] == "resume" for q in questions):     # older reports (no resume questions) keep exactly their old shape
        out["resume_claims"] = claims
    out["intelligence"] = intelligence(questions, out["skills"])
    keys = iv.keys()
    plan = json.loads(iv["plan_json"]) if "plan_json" in keys and iv["plan_json"] else {}
    out["interview"]["end_reason"] = iv["end_reason"] if "end_reason" in keys else None
    out["adaptive"] = adaptive_summary(c, iv) if out["interview"]["config"].get("mode") == "adaptive" else None
    coverage = resume_coverage(plan, questions)
    if coverage:
        out["resume_coverage"] = coverage
    return out


# ----------------------------------------------------------------------- Interview Intelligence 2.0 analytics
CONCEPTUAL_DIMS = ("correctness", "conceptual_understanding", "depth")
PRACTICAL_DIMS = ("practical_application", "problem_solving", "edge_cases", "production_awareness")
SKILL_ADVICE = {
    "correctness": "Re-learn the fundamentals behind the questions you got wrong; check each claim you make against a reliable source.",
    "completeness": "Before answering, list the 3-4 essential points the question needs, then cover each one.",
    "depth": "After each 'what', add the 'why' and 'how': explain the mechanism, not just the definition.",
    "practical_application": "Prepare one concrete example from your own work for each core concept.",
    "clarity": "Structure answers: one-line answer first, then reasons, then an example. Practise out loud.",
    "production_awareness": "For every design, say how it is monitored, how it fails and what it costs at scale.",
    "conceptual_understanding": "Draw the underlying model (data flow, memory, set semantics) before memorising syntax.",
    "problem_solving": "Talk through your approach: restate the problem, outline options, pick one and justify it.",
    "edge_cases": "Practise naming edge cases out loud: empty input, NULLs, duplicates, concurrency, limits, failures.",
    "tradeoffs": "For each choice, name one alternative and compare them on cost, complexity and risk.",
}
CLASS_ORDER = ["correct", "correct_incomplete", "partially_correct", "incorrect", "no_attempt", "uncertain"]


def _evaluated_turns(questions: list[dict]):
    for q in questions:
        for t in q["turns"]:
            if t.get("status") == "evaluated" and t.get("evaluation"):
                yield q, t, t["evaluation"]


def _avg(values: list[float]) -> Optional[float]:
    return round(sum(values) / len(values), 1) if values else None


def intelligence(questions: list[dict], skills: list[dict]) -> dict[str, Any]:
    """Deterministic analytics over the stored evaluations. Older evaluations (before v6) simply contribute less detail."""
    classes: Counter = Counter()
    by_diff: dict[str, list[float]] = {}
    conceptual: list[float] = []
    practical: list[float] = []
    profiles: dict[str, dict[str, Any]] = {}
    evidence_total = evidence_verified = 0
    flags: Counter = Counter()
    adjustments: list[str] = []
    unverified = 0
    for q, t, ev in _evaluated_turns(questions):
        if ev.get("classification"):
            classes[ev["classification"]] += 1
        dims = ev.get("dimension_scores") or {}
        conceptual += [float(dims[d]) for d in CONCEPTUAL_DIMS if dims.get(d) is not None]
        practical += [float(dims[d]) for d in PRACTICAL_DIMS if dims.get(d) is not None and (d != "production_awareness" or ev.get("production_relevant"))]
        if ev.get("profile"):
            p = profiles.setdefault(ev["profile"], {"key": ev["profile"], "label": ev.get("profile_label") or ev["profile"], "answers": 0, "scores": []})
            p["answers"] += 1
            if t.get("score") is not None:
                p["scores"].append(float(t["score"]))
        for e in ev.get("evidence") or []:
            evidence_total += 1
            evidence_verified += 1 if e.get("verified") else 0
        for f in ev.get("consistency_flags") or []:
            flags[f.get("code", "other")] += 1
        adjustments += [f"Q{q['position']}: {a}" for a in ev.get("adjustments") or []]
        unverified += len(ev.get("unverified_misconceptions") or [])
    for q in questions:
        if q["score"] is not None:
            by_diff.setdefault((q["difficulty"] or "unrated").lower(), []).append(q["score"])
    difficulty = [{"difficulty": d, "questions": len(v), "average_score": _avg(v)} for d, v in
                  sorted(by_diff.items(), key=lambda kv: ["easy", "medium", "hard", "unrated"].index(kv[0]) if kv[0] in ("easy", "medium", "hard", "unrated") else 9)]
    c_avg, p_avg = _avg(conceptual), _avg(practical)
    balance = None
    if c_avg is not None and p_avg is not None:
        balance = ("Practical application lags conceptual understanding." if c_avg - p_avg >= 1.5 else
                   "Conceptual understanding lags practical experience." if p_avg - c_avg >= 1.5 else "Conceptual and practical skills are balanced.")
    scored_skills = [k for k in skills if k["average"] is not None and k["answers"] > 0]
    weakest = sorted(scored_skills, key=lambda k: k["average"])[:3]
    plan = [{"skill": k["label"], "average": k["average"], "action": SKILL_ADVICE.get(k["key"], "")} for k in weakest if k["average"] < 7.5]
    return {
        "classifications": [{"key": k, "count": classes[k]} for k in CLASS_ORDER if classes.get(k)],
        "difficulty": difficulty,
        "conceptual_vs_practical": {"conceptual": c_avg, "practical": p_avg, "summary": balance},
        "profiles": [{**{k: v for k, v in p.items() if k != "scores"}, "average_score": _avg(p["scores"])} for p in profiles.values()],
        "evidence": {"quotes": evidence_total, "verified": evidence_verified, "unverified_misconceptions": unverified},
        "consistency": {"flags": [{"code": k, "count": v} for k, v in flags.most_common()], "adjustments": adjustments[:10]},
        "learning_plan": plan,
    }


def adaptive_summary(c: sqlite3.Connection, iv) -> dict[str, Any]:
    config = json.loads(iv["config_json"])
    state = json.loads(iv["adaptive_json"]) if iv["adaptive_json"] else {}
    events = [dict(r) for r in c.execute("""SELECT e.kind, e.decision, e.reason, e.level_before, e.level_after, e.topic, e.created_at,
                                            (SELECT position FROM interview_items WHERE id=e.item_id) AS position
                                            FROM adaptive_events e WHERE e.interview_id=? ORDER BY e.id""", (iv["id"],))]
    for e in events:
        e["question"] = e.pop("position") + 1 if e.get("position") is not None else None
    levels = ["beginner", "intermediate", "advanced", "expert"]
    unused = c.execute("SELECT COUNT(*) FROM interview_pool WHERE interview_id=? AND status='available'", (iv["id"],)).fetchone()[0]
    return {"strategy": config.get("strategy"), "start_level": config.get("start_level"),
            "final_level": levels[int(state.get("level", 1))] if state else config.get("start_level"),
            "level_history": state.get("level_history", []), "events": events, "pool_unused": unused, "end_reason": iv["end_reason"]}


def resume_coverage(plan: dict[str, Any], questions: list[dict]) -> Optional[dict[str, Any]]:
    inventory = plan.get("resume_inventory") or []
    asked = [q for q in questions if q.get("source") == "resume"]
    if not inventory and not asked:
        return None
    discussed = {((q.get("claim") or {}).get("label") or "") for q in asked if q["status"] in ("answered", "skipped")}
    def hit(label: str) -> bool:
        # AI-written resume questions label a bullet group "<role>: <first bullet>"; anything else must match exactly
        return bool(label) and any(d == label or d.startswith(label + ": ") for d in discussed if d)
    unexplored = [ci for ci in inventory if not hit(ci.get("label") or "")]
    return {"claims_total": len(inventory), "claims_discussed": len(inventory) - len(unexplored), "unexplored": unexplored[:20],
            "questions": len(asked)}


def _load_claim(raw: Optional[str]) -> Optional[dict[str, Any]]:
    try:
        claim = json.loads(raw) if raw else None
    except ValueError:
        return None
    return claim if isinstance(claim, dict) else None


CLAIM_VERDICTS = [(7.0, "Solid"), (5.0, "Shaky"), (0.0, "Weak")]


def claim_verdict(score: float) -> str:
    return next(label for floor, label in CLAIM_VERDICTS if score >= floor)


def _claim_tip(qs: list[dict], average: float) -> str:
    """One plain sentence from what the grader already wrote (suggested improvements first, then missing points)."""
    evs = [t["evaluation"] for q in qs for t in q["turns"] if t.get("evaluation")]
    improve = next((x for e in evs for x in e.get("suggested_improvements", []) if x), None)
    missing = next((x for e in evs for x in e.get("missing_concepts", []) if x), None)
    if average >= 7:
        return "Well defended. Keep using the same concrete details, numbers and decisions."
    if improve:
        return improve.rstrip(".") + "."
    if missing:
        return f"Be more concrete about: {missing.rstrip('.')}."
    return "Prepare a specific story: your own part, a decision you made, how the result was measured and what you learned."


def resume_claims(questions: list[dict]) -> list[dict[str, Any]]:
    """Each resume claim that was defended: average of its SCORED questions (skipped / not reached never count), verdict and a tip.
    Weakest first. Computed in code; the model never decides a verdict."""
    groups: dict[tuple, list[dict]] = {}
    for q in questions:
        if q.get("source") != "resume":
            continue
        claim = q.get("claim") or {}
        key = (q.get("resume_id"), q.get("resume_name") or "", claim.get("section") or "", claim.get("label") or "")
        groups.setdefault(key, []).append(q)
    out = []
    for (rid, rname, section, label), qs in groups.items():
        scored = [q["score"] for q in qs if q["score"] is not None]
        if not scored:
            continue
        avg = round(sum(scored) / len(scored), 1)
        out.append({"resume_id": rid, "resume_name": rname, "section": section, "label": label, "average_score": avg, "verdict": claim_verdict(avg),
                    "questions": len(qs), "scored": len(scored), "question_numbers": [q["position"] for q in qs], "tip": _claim_tip(qs, avg)})
    out.sort(key=lambda c: (c["average_score"], c["label"]))
    return out


def rule_based_insights(questions: list[dict], topics: list[dict], summary: dict) -> dict[str, Any]:
    scored_topics = [t for t in topics if t["average_score"] is not None]
    strengths = [f"{t['topic']} (average {t['average_score']}/10)" for t in scored_topics if t["average_score"] >= 7][:5]
    for q in sorted((q for q in questions if q["score"] is not None and q["score"] >= 7), key=lambda q: -q["score"]):
        pts = next((t["evaluation"]["correct_points"][0] for t in q["turns"]
                    if t["evaluation"] and t["evaluation"].get("correct_points")), None)
        if pts and len(strengths) < 6:
            strengths.append(f"Q{q['position']}: {pts}")

    missing, miscon = [], []
    for q in questions:
        for t in q["turns"]:
            ev = t["evaluation"] or {}
            missing += [(m, q["position"]) for m in ev.get("missing_concepts", [])]
            miscon += [(m, q["position"]) for m in ev.get("misconceptions", [])]
    gap_clusters = sorted(_cluster(missing), key=lambda c: -len(c["questions"]))
    gaps = [(f"{c['text']}" + (f" (in {len(c['questions'])} questions)" if len(c["questions"]) > 1 else ""))
            for c in gap_clusters][:6]
    repeated = [f"{c['text']} (Q{', Q'.join(str(n) for n in sorted(c['questions']))})"
                for c in sorted(_cluster(miscon), key=lambda c: -len(c["questions"])) if len(c["questions"]) > 1][:5]

    revise = [t["topic"] for t in scored_topics if t["average_score"] < 6.5]
    if not revise and scored_topics and scored_topics[0]["average_score"] < 8:
        revise = [scored_topics[0]["topic"]]

    recs = []
    for name in revise[:4]:
        qs = [q for q in questions if (q["topic"] or UNCATEGORIZED) == name]
        want = [m for q in qs for t in q["turns"] for m in ((t["evaluation"] or {}).get("missing_concepts", []))][:2]
        recs.append(f"Revise {name}" + (f": focus on {'; '.join(want)}." if want else "."))
    if summary["skipped"] or summary["unanswered"]:
        recs.append(f"Revisit the {summary['skipped'] + summary['unanswered']} question(s) you skipped or did not reach.")
    if summary["scored"] == 0:
        recs.append("No answers were evaluated, so there is not enough evidence for a skills assessment yet.")
    elif not recs:
        recs.append("Keep practicing with harder or scenario-style questions to stay sharp.")

    if summary["average_score"] is None:
        text = "No answers were scored in this session."
    else:
        text = (f"Average {summary['average_score']}/10 across {summary['scored']} scored question(s)"
                f" ({summary['answered']} answered, {summary['skipped']} skipped, {summary['unanswered']} not reached).")
    return {"overall_summary": text, "strengths": strengths, "knowledge_gaps": gaps,
            "repeated_misconceptions": repeated, "topics_to_revise": revise, "recommendations": recs}


def narrative_digest(data: dict[str, Any]) -> Optional[str]:
    lines = []
    for q in data["questions"]:
        if q["score"] is None:
            continue
        ev = [t["evaluation"] for t in q["turns"] if t["evaluation"]]
        correct = [p for e in ev for p in e.get("correct_points", [])][:2]
        missing = [p for e in ev for p in e.get("missing_concepts", [])][:3]
        wrong = [p for e in ev for p in e.get("misconceptions", [])][:2]
        lines.append(f"Q{q['position']} [{q['topic'] or UNCATEGORIZED}] score {q['score']}/10. "
                     f"Correct: {'; '.join(correct) or '-'}. Missing: {'; '.join(missing) or '-'}. "
                     f"Misconceptions: {'; '.join(wrong) or '-'}.")
    if not lines:
        return None
    s = data["summary"]
    head = (f"Interview '{data['interview']['title']}'. {s['total_questions']} questions: {s['answered']} answered, "
            f"{s['skipped']} skipped, {s['unanswered']} not reached. Average {s['average_score']}/10.\n"
            "Topic averages: " + ", ".join(f"{t['topic']}={t['average_score']}" for t in data["topics"] if t["average_score"] is not None))
    return (head + "\n\n" + "\n".join(lines))[:6000]


# ----------------------------------------------------------------------- persistence
def store_report(c: sqlite3.Connection, iid: int) -> None:
    data = build_report(c, iid)
    now = utcnow()
    c.execute("""INSERT INTO reports(interview_id, data_json, narrative_status, created_at, updated_at)
                 VALUES (?,?, 'pending', ?, ?)
                 ON CONFLICT(interview_id) DO UPDATE SET data_json=excluded.data_json, updated_at=excluded.updated_at""",
              (iid, json.dumps(data, ensure_ascii=False), now, now))


def get_report(db: Database, iid: int) -> dict[str, Any]:
    with db.read() as c:
        row = c.execute("SELECT * FROM reports WHERE interview_id=?", (iid,)).fetchone()
    if not row:
        raise not_found("Report (the interview may still be running)")
    data = json.loads(row["data_json"])
    data["narrative_status"] = row["narrative_status"]
    data["narrative_error"] = row["narrative_error"]
    data["insights"] = data["narrative"] or data["aggregated"]
    data["insights_source"] = "model" if data["narrative"] else "rules"
    data["report_created_at"] = row["created_at"]
    _mark_deleted_resumes(db, data)
    data["progress"] = topic_progress(db, iid, data.get("topics") or [])
    return data


def topic_progress(db: Database, iid: int, topics: list[dict]) -> list[dict[str, Any]]:
    """For each scored topic: the average in the most recent EARLIER report that covered it, and the change since."""
    want = {t["topic"]: t["average_score"] for t in topics if t["average_score"] is not None}
    if not want:
        return []
    with db.read() as c:
        rows = c.execute("SELECT interview_id, data_json FROM reports WHERE interview_id < ? ORDER BY interview_id DESC LIMIT 50", (iid,)).fetchall()
    prev: dict[str, tuple[int, float]] = {}
    for r in rows:
        try:
            older = json.loads(r["data_json"]).get("topics") or []
        except ValueError:
            continue
        for t in older:
            if t.get("topic") in want and t["topic"] not in prev and t.get("average_score") is not None:
                prev[t["topic"]] = (r["interview_id"], t["average_score"])
    return [{"topic": k, "average_score": v, "previous": prev[k][1] if k in prev else None, "previous_interview_id": prev[k][0] if k in prev else None,
             "delta": round(v - prev[k][1], 1) if k in prev else None} for k, v in want.items()]


def _mark_deleted_resumes(db: Database, data: dict[str, Any]) -> None:
    """A report keeps working after its resume is deleted: the snapshot stays, and the UI says "(deleted resume)"."""
    ids = {q.get("resume_id") for q in data["questions"] if q.get("source") == "resume" and q.get("resume_id") is not None}
    ids |= {c.get("resume_id") for c in data.get("resume_claims") or [] if c.get("resume_id") is not None}
    if not ids:
        return
    with db.read() as c:
        alive = {r[0] for r in c.execute(f"SELECT id FROM resumes WHERE id IN ({','.join('?' * len(ids))})", tuple(ids))}
    for q in data["questions"]:
        if q.get("source") == "resume":
            q["resume_deleted"] = q.get("resume_id") is None or q.get("resume_id") not in alive
    for cl in data.get("resume_claims") or []:
        cl["resume_deleted"] = cl.get("resume_id") is None or cl.get("resume_id") not in alive


REDACTED = "[redacted]"
_SAFE_EVAL_KEYS = ("dimension_scores", "production_relevant", "question_level", "confidence", "profile", "profile_label", "weights",
                   "classification", "followup_asked", "followup_kind")


def redact(data: dict[str, Any]) -> dict[str, Any]:
    """A shareable copy of a report, built by ALLOW-LIST: scores, classifications, topics and generic advice only.

    Removed: the candidate's answers and everything the grader wrote about them (it quotes and paraphrases the answer), follow-up
    questions (they build on the answer), the model-written narrative, resume names, labels and excerpts, the text of resume
    questions, decision reasons (they name resume claims), and model usage. Bank question texts are kept: they are the user's
    own practice questions, not the candidate's words."""
    src = data
    out: dict[str, Any] = {"redacted": True}
    iv = src.get("interview") or {}
    cfg = iv.get("config") or {}
    out["interview"] = {k: iv.get(k) for k in ("id", "title", "type", "status", "created_at", "completed_at", "end_reason")}
    out["interview"]["config"] = {k: cfg.get(k) for k in ("interview_type", "mode", "strategy", "start_level", "strictness", "max_followups",
                                                           "time_limit_minutes", "max_questions") if k in cfg}
    out["summary"] = dict(src.get("summary") or {})
    out["topics"] = [{k: t.get(k) for k in ("topic", "questions", "scored", "average_score", "question_numbers")} for t in src.get("topics") or []]
    out["skills"] = [dict(k) for k in src.get("skills") or []]
    out["scoring_rules"] = list(src.get("scoring_rules") or [])
    out["progress"] = [dict(p) for p in src.get("progress") or []]
    questions = []
    for q in src.get("questions") or []:
        resume = q.get("source") == "resume"
        nq = {k: q.get(k) for k in ("position", "topic", "difficulty", "status", "score", "verdict", "followups_asked", "source")}
        nq["text"] = "[resume question]" if resume else q.get("text", "")
        if resume:
            nq["topic"] = "Resume"
        turns = []
        for t in q.get("turns") or []:
            ev = t.get("evaluation")
            nt = {"seq": t.get("seq"), "kind": t.get("kind"), "status": t.get("status"), "score": t.get("score"), "source": t.get("source"),
                  "question": (nq["text"] if t.get("kind") == "main" else "[follow-up question]"),
                  "answer": REDACTED if t.get("answer") else t.get("answer"), "followup_reason": None,
                  "evaluation": ({k: ev.get(k) for k in _SAFE_EVAL_KEYS if k in ev} | {"score": ev.get("score"), "verdict": ev.get("verdict")}) if ev else None}
            turns.append(nt)
        nq["turns"] = turns
        questions.append(nq)
    out["questions"] = questions
    # rule-based numbers and topic names only; no model prose (it paraphrases answers)
    scored = (out["summary"] or {}).get("average_score")
    out["insights"] = {"overall_summary": (f"Average {scored}/10 across {out['summary'].get('scored')} scored question(s)." if scored is not None
                                           else "No answers were scored in this session."),
                       "strengths": [], "knowledge_gaps": [], "repeated_misconceptions": [],
                       "topics_to_revise": [t for t in ((src.get("aggregated") or {}).get("topics_to_revise") or [])
                                            if t in {x["topic"] for x in out["topics"]}], "recommendations": []}
    out["insights_source"] = "rules"
    out["narrative"] = None
    out["aggregated"] = out["insights"]
    out["narrative_status"] = "ready"
    out["narrative_error"] = None
    intel = src.get("intelligence")
    if intel:
        out["intelligence"] = {k: intel.get(k) for k in ("classifications", "difficulty", "conceptual_vs_practical", "profiles", "learning_plan")}
        out["intelligence"]["evidence"] = {"quotes": 0, "verified": 0, "unverified_misconceptions": 0}
        out["intelligence"]["consistency"] = {"flags": (intel.get("consistency") or {}).get("flags", []), "adjustments": []}
    ad = src.get("adaptive")
    if ad:
        out["adaptive"] = {k: ad.get(k) for k in ("strategy", "start_level", "final_level", "pool_unused", "end_reason")}
        out["adaptive"]["level_history"] = [{k: h.get(k) for k in ("from", "to", "after_question")} for h in ad.get("level_history") or []]
        out["adaptive"]["events"] = [{"kind": e.get("kind"), "decision": e.get("decision"), "question": e.get("question"),
                                      "level_before": e.get("level_before"), "level_after": e.get("level_after"),
                                      "reason": e.get("decision", "").replace("_", " ")} for e in ad.get("events") or []]
    else:
        out["adaptive"] = None
    return out


def set_narrative(db: Database, iid: int, narrative: Optional[dict], status: str, error: Optional[str]) -> None:
    with db.tx() as c:
        row = c.execute("SELECT data_json FROM reports WHERE interview_id=?", (iid,)).fetchone()
        if not row:
            return  # interview deleted meanwhile
        data = json.loads(row["data_json"])
        if narrative is not None:
            data["narrative"] = narrative
        c.execute("UPDATE reports SET data_json=?, narrative_status=?, narrative_error=?, updated_at=? WHERE interview_id=?",
                  (json.dumps(data, ensure_ascii=False), status, error, utcnow(), iid))


# ----------------------------------------------------------------------- markdown
def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {i}" for i in items) if items else "_None identified._"


def _md_cell(text: str) -> str:
    return str(text).replace("|", "/").replace("\n", " ")


def claim_title(c: dict[str, Any], with_section: bool = True) -> str:
    """"Resume 1 › Experience › Backend engineer at Acme" (or "(deleted resume)" when the resume is gone)."""
    claim = c.get("claim") if "claim" in c else c
    claim = claim or {}
    name = c.get("resume_name") or "Resume"
    if c.get("resume_deleted"):
        name += " (deleted resume)"
    parts = [name] + ([claim.get("section")] if with_section and claim.get("section") else []) + ([claim.get("label")] if claim.get("label") else [])
    return " › ".join(p for p in parts if p)


def render_markdown(r: dict[str, Any]) -> str:
    s, iv = r["summary"], r["interview"]
    ins = r["insights"]
    avg = f"{s['average_score']}/10 ({s['verdict']})" if s["average_score"] is not None else "n/a (no scored answers)"
    out = [f"# Interview report: {iv['title']}", "",
           f"- Type: {iv['type']}  \n- Status: {iv['status']}  \n- Started: {iv['created_at']}  \n- Finished: {iv['completed_at'] or '-'}", "",
           "## Summary", "",
           f"| Total questions | Answered | Skipped | Not reached | Scored | Average score |\n|---|---|---|---|---|---|\n"
           f"| {s['total_questions']} | {s['answered']} | {s['skipped']} | {s['unanswered']} | {s['scored']} | {avg} |", "",
           ins["overall_summary"], ""]
    out += ["### Scoring rules", "", _bullets(r["scoring_rules"]), ""]
    out += ["## Topic performance", "", "| Topic | Questions | Scored | Average |", "|---|---|---|---|"]
    for t in r["topics"]:
        out.append(f"| {t['topic']} | {t['questions']} | {t['scored']} | {t['average_score'] if t['average_score'] is not None else '-'} |")
    if r.get("resume_claims"):
        out += ["", "## Resume claims", "", "How well you defended what your resume says (weakest first).", "",
                "| Claim | Questions | Average | Verdict | Tip |", "|---|---|---|---|---|"]
        for c in r["resume_claims"]:
            out.append(f"| {_md_cell(claim_title(c))} | {', '.join(f'Q{n}' for n in c['question_numbers'])} | {c['average_score']} | {c['verdict']} | {_md_cell(c['tip'])} |")
    out += ["", "## Strengths", "", _bullets(ins["strengths"]), "", "## Knowledge gaps", "", _bullets(ins["knowledge_gaps"]), "",
            "## Repeated misconceptions", "", _bullets(ins["repeated_misconceptions"]), "",
            "## Topics to revise", "", _bullets(ins["topics_to_revise"]), "",
            "## Recommendations", "", _bullets(ins["recommendations"]), ""]
    intel = r.get("intelligence") or {}
    if intel.get("classifications") or intel.get("learning_plan"):
        out += ["## Assessment detail", ""]
        if intel.get("classifications"):
            out += ["Answer classification: " + ", ".join(f"{c['key'].replace('_', ' ')} {c['count']}" for c in intel["classifications"]), ""]
        cvp = intel.get("conceptual_vs_practical") or {}
        if cvp.get("summary"):
            out += [f"Conceptual {cvp['conceptual']}/10 vs practical {cvp['practical']}/10. {cvp['summary']}", ""]
        if intel.get("difficulty"):
            out += ["| Difficulty | Questions | Average |", "|---|---|---|"] + [f"| {d['difficulty']} | {d['questions']} | {d['average_score']} |" for d in intel["difficulty"]] + [""]
        if intel.get("learning_plan"):
            out += ["### Learning plan", ""] + [f"- **{p['skill']}** ({p['average']}/10): {p['action']}" for p in intel["learning_plan"]] + [""]
    ad = r.get("adaptive")
    if ad:
        out += ["## Adaptive interview", "", f"Strategy: {ad['strategy']} · level {ad['start_level']} → {ad['final_level']} · ended: {ad.get('end_reason') or '-'}", ""]
        out += [f"- {('Q' + str(e['question']) + ': ') if e.get('question') else ''}{e['reason']}" for e in ad["events"]] + [""]
    cov = r.get("resume_coverage")
    if cov and cov.get("claims_total"):
        out += ["## Resume coverage", "", f"{cov['claims_discussed']} of {cov['claims_total']} resume roles/projects discussed.", ""]
        if cov["unexplored"]:
            out += ["Not yet explored:", _bullets([f"{u.get('section')}: {u.get('label')}" for u in cov["unexplored"]]), ""]
    out += ["## Scorecard", "", "| # | Question | Answer | Follow-ups | Question score |", "|---|---|---|---|---|"]
    for q in r["questions"]:
        main = next((t for t in q["turns"] if t["kind"] == "main"), None)
        ans = "skipped" if q["status"] == "skipped" else (str(main["score"]) if main and main["score"] is not None else "-")
        fus = ", ".join(f"{t['score'] if t['score'] is not None else ('skipped' if t['status'] == 'skipped' else '-')}" for t in q["turns"] if t["kind"] != "main") or "-"
        text = q["text"].replace("|", "/").replace("\n", " ")
        text = text if len(text) <= 80 else text[:79] + "…"
        out.append(f"| {q['position']} | {text} | {ans} | {fus} | {q['score'] if q['score'] is not None else q['status']} |")
    out += [f"| | **Final score** | | | **{avg}** |", ""]
    skills = [k for k in r.get("skills", []) if k["average"] is not None]
    if skills:
        out += ["## Skills", "", "| Skill | Average | Answers |", "|---|---|---|"]
        out += [f"| {k['label']} | {k['average']} | {k['answers']} |" for k in skills]
        out.append("")
    out += ["## Questions", ""]
    for q in r["questions"]:
        score = f"{q['score']}/10 ({q['verdict']})" if q["score"] is not None else q["status"]
        resume_tag = f" | Resume: {claim_title(q, with_section=False)}" if q.get("source") == "resume" else ""
        out += [f"### Q{q['position']}. {q['text']}", "",
                f"_Topic: {q['topic'] or UNCATEGORIZED} | Difficulty: {q['difficulty'] or '-'} | Result: {score}{resume_tag}_", ""]
        for t in q["turns"]:
            if t["kind"] != "main":
                out += [f"**Follow-up:** {t['question']}", ""]
            if t["status"] == "skipped":
                out += ["_Skipped._", ""]
                continue
            out += [f"**Answer:** {t['answer'] or '_(no answer)_'}", ""]
            ev = t["evaluation"]
            if ev:
                out += [f"**Score:** {t['score']}/10", ""]
                for title, key in (("Correct points", "correct_points"), ("Missing", "missing_concepts"),
                                   ("Misconceptions", "misconceptions"),
                                   ("Possible errors (not found in the answer; not counted)", "unverified_misconceptions"),
                                   ("Suggested improvements", "suggested_improvements")):
                    if ev.get(key):
                        out += [f"**{title}:**", _bullets(ev[key]), ""]
                if ev.get("ideal_answer"):
                    out += [f"**Reference answer:** {ev['ideal_answer']}", ""]
                if ev.get("uncertainty_note"):
                    out += [f"_Evaluation note ({ev.get('confidence')} confidence): {ev['uncertainty_note']}_", ""]
            elif t["status"] == "submitted":
                out += ["_Not evaluated (model error)._", ""]
    return "\n".join(x for x in out if x is not None).rstrip() + "\n"
