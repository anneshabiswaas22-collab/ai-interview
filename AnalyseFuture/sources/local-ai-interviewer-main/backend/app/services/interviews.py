"""Interview state machine.

Persisted state per interview:
    status: in_progress | paused | completed | ended
    phase : awaiting_answer -> evaluating -> (evaluation_failed) -> feedback -> awaiting_answer ... -> done

Rules that make it safe:
  * every transition runs inside one BEGIN IMMEDIATE transaction and checks the expected status/phase/turn
    (compare-and-set), so duplicate or stale requests get a 409 instead of changing state;
  * an answer is written *before* evaluation starts and is never discarded on failure;
  * evaluation runs on a single worker thread; its result is applied only if the interview is still waiting
    for exactly that turn;
  * the follow-up limit is read from the interview's frozen config and enforced in code at turn creation.
"""
from __future__ import annotations

import json
import logging
import random
import sqlite3
from concurrent.futures import Executor, ThreadPoolExecutor
from datetime import datetime
from typing import Any, Callable, Optional

from ..db import Database, utcnow
from ..errors import AppError, bad_request, conflict, not_found
from ..parsing import normalize_for_dedupe
from ..schemas import (MAX_ANSWER_CHARS, MAX_INTERVIEW_QUESTIONS, MAX_POOL_QUESTIONS, AnswerIn, ClaimIn, InterviewConfig, LLMEvaluation,
                       ResumeAutoIn, ResumeQuestionIn)
from . import adaptive, eval_profiles, reports
from .evaluator import EvalContext, Evaluator, FollowUpDecision, decide_followup, is_non_attempt, question_level, too_similar
from .ollama import LLMError
from .questions import QuestionService
from .usage import usage_context

log = logging.getLogger("interviewer.interviews")

ACTIVE = ("in_progress", "paused")


class InterviewService:
    def __init__(self, db: Database, questions: QuestionService, evaluator: Evaluator,
                 executor: Optional[Executor] = None):
        self.db = db
        self.questions = questions
        self.evaluator = evaluator
        self.executor: Executor = executor or ThreadPoolExecutor(max_workers=1, thread_name_prefix="llm")
        self.busy_checks: list = []          # other model work (resume jobs) that must finish before the model is unloaded
        # resume intelligence hooks (set by deps.build_container): offline claim-grounded questions and a resume's claim inventory
        self.auto_questions: Optional[Callable[[int, int, list[str]], list[dict[str, Any]]]] = None
        self.claim_inventory: Optional[Callable[[int], list[dict[str, Any]]]] = None
        self.recover()

    # ================================================================ lifecycle
    def recover(self) -> None:
        """After a crash/restart nothing may stay 'evaluating' forever; answers stay saved for Retry."""
        with self.db.tx() as c:
            c.execute("""UPDATE interviews SET phase='evaluation_failed', updated_at=?,
                         error='Evaluation was interrupted by an app restart. Your answer is saved - press Retry.'
                         WHERE phase='evaluating'""", (utcnow(),))
            c.execute("""UPDATE reports SET narrative_status='failed', updated_at=?,
                         narrative_error='Interrupted by an app restart. Use "Regenerate summary".'
                         WHERE narrative_status='pending'""", (utcnow(),))

    def create(self, set_id: Optional[int], config: InterviewConfig, resume_questions: Optional[list[ResumeQuestionIn]] = None,
               resume_auto: Optional[ResumeAutoIn] = None) -> dict[str, Any]:
        """Build the question list (bank questions as before, plus reviewed resume questions) and start the interview in ONE transaction.

        Fixed mode: the list is the interview, asked in order (unchanged since v1). Adaptive mode: the list becomes a pool and the
        adaptive engine picks each next question from it (services/adaptive.py)."""
        resume_questions = list(resume_questions or [])
        if resume_auto is not None:          # offline, claim-grounded questions from the candidate profile (no model call)
            if self.auto_questions is None:
                raise bad_request("resume_auto_unavailable", "Automatic resume questions are not available.")
            taken = [q.text for q in resume_questions]
            for q in self.auto_questions(resume_auto.resume_id, resume_auto.count, taken):
                resume_questions.append(ResumeQuestionIn(text=q["text"], rubric=q.get("rubric"), topic=q.get("topic"), difficulty=q.get("difficulty"),
                                                         kind=q.get("kind"), resume_id=q.get("resume_id"), resume_name=q.get("resume_name"),
                                                         claim=ClaimIn(**q["claim"]) if q.get("claim") else None))
        bank: list[dict[str, Any]] = []
        if config.include_bank and set_id is not None:
            qs = self.questions.list_questions(set_id)
            if config.question_ids is not None:
                wanted = list(dict.fromkeys(config.question_ids))
                by_id = {q["id"]: q for q in qs}
                unknown = [i for i in wanted if i not in by_id]
                if unknown:
                    raise bad_request("unknown_questions", f"Questions not in this set: {unknown}")
                qs = [by_id[i] for i in wanted if i in by_id]
                qs.sort(key=lambda q: q["position"])  # "supplied order" = the queue order, not click order
            if config.order == "shuffled":
                random.SystemRandom().shuffle(qs)
            bank = [{"question_id": q["id"], "text": q["text"], "rubric": q["rubric"], "topic": q["topic"], "difficulty": q["difficulty"],
                     "source": "bank", "resume_id": None, "resume_name": None, "claim_json": None} for q in qs]
        resume_items = [{"question_id": None, "text": rq.text, "rubric": rq.rubric, "topic": rq.topic, "difficulty": rq.difficulty, "source": "resume",
                         "resume_id": rq.resume_id, "resume_name": rq.resume_name, "claim_json": rq.claim.model_dump_json() if rq.claim else None}
                        for rq in (resume_questions or [])]
        items = mix_items(bank, resume_items, config.mix)
        # a resume question that repeats a bank question or another resume question (e.g. reviewed + offline) is asked once;
        # bank questions are never dropped (fixed-mode behaviour is unchanged)
        seen = {normalize_for_dedupe(b["text"]) for b in bank}
        unique: list[dict[str, Any]] = []
        for it in items:
            if it["source"] == "resume":
                key = normalize_for_dedupe(it["text"])
                if key in seen:
                    continue
                seen.add(key)
            unique.append(it)
        items = unique
        if not items:
            raise bad_request("no_questions", "Add or select at least one question before starting an interview.")
        adaptive_mode = config.mode == "adaptive"
        limit = MAX_POOL_QUESTIONS if adaptive_mode else MAX_INTERVIEW_QUESTIONS
        if len(items) > limit:
            raise bad_request("too_many_questions", f"An interview can have at most {limit} questions (you chose {len(items)}).")
        if adaptive_mode and config.strategy == "resume" and not any(it["source"] == "resume" for it in items):
            raise bad_request("no_resume_questions", "A resume-based interview needs questions from a resume. Pick a resume or another strategy.")
        plan = self._plan(config, items)
        now = utcnow()
        with self.db.tx() as c:
            active = c.execute("SELECT id, title FROM interviews WHERE status IN ('in_progress','paused') ORDER BY id DESC LIMIT 1").fetchone()
            if active:     # one interview at a time: finish or end the current one first
                raise conflict("interview_active", f"“{active['title']}” is still active. Continue it, or end it, before starting a new interview.", interview_id=active["id"])
            names: dict[int, str] = {}
            wanted_resumes = {it["resume_id"] for it in items if it["resume_id"] is not None}
            if wanted_resumes:              # the resume's own current name is the snapshot, never what the browser sent
                rows = c.execute(f"SELECT id, name FROM resumes WHERE id IN ({','.join('?' * len(wanted_resumes))})", tuple(wanted_resumes)).fetchall()
                names = {r["id"]: r["name"] for r in rows}
                missing = sorted(wanted_resumes - set(names))
                if missing:
                    raise bad_request("unknown_resume", "A resume these questions came from no longer exists. Generate the questions again.")
            state = adaptive.EngineState(level=adaptive.LEVELS.index(config.start_level)) if adaptive_mode else None
            cur = c.execute("""INSERT INTO interviews(set_id, title, interview_type, status, phase, config_json,
                               created_at, started_at, updated_at, plan_json, adaptive_json) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                            (set_id if bank else None, config.title, config.interview_type, "in_progress", "awaiting_answer",
                             config.model_dump_json(), now, now, now, json.dumps(plan), json.dumps(state.dump()) if state else None))
            iid = cur.lastrowid
            for pos, q in enumerate(items):
                resume_name = names.get(q["resume_id"], q["resume_name"]) if q["resume_id"] is not None else q["resume_name"]
                if adaptive_mode:
                    c.execute("""INSERT INTO interview_pool(interview_id, ord, question_id, text, rubric, topic, difficulty, source, resume_id,
                                 resume_name, claim_json) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                              (iid, pos, q["question_id"], q["text"], q["rubric"], q["topic"], q["difficulty"], q["source"], q["resume_id"],
                               resume_name, q["claim_json"]))
                else:
                    c.execute("""INSERT INTO interview_items(interview_id, position, question_id, text, rubric, topic,
                                 difficulty, status, created_at, source, resume_id, resume_name, claim_json) VALUES (?,?,?,?,?,?,?,'pending',?,?,?,?,?)""",
                              (iid, pos, q["question_id"], q["text"], q["rubric"], q["topic"], q["difficulty"], now,
                               q["source"], q["resume_id"], resume_name, q["claim_json"]))
            iv = self._row(c, iid)
            if not self._activate_next(c, iv):
                raise bad_request("no_questions", "None of the selected questions could be asked.")
        return self.get_state(iid)

    def _plan(self, config: InterviewConfig, items: list[dict[str, Any]]) -> dict[str, Any]:
        """The interview plan: objectives (topics to cover) and, for resume questions, the claims that could be discussed."""
        topics: list[str] = []
        for it in items:
            t = adaptive.topic_of(it["topic"])
            if t not in topics:
                topics.append(t)
        inventory: list[dict[str, Any]] = []
        for rid in dict.fromkeys(it["resume_id"] for it in items if it["resume_id"] is not None):
            try:
                inventory += [{**ci, "resume_id": rid} for ci in (self.claim_inventory(rid) if self.claim_inventory else [])]
            except Exception:             # the plan is informative; a resume that cannot be profiled never blocks an interview
                log.info("claim inventory unavailable for resume %s", rid)
        return {"mode": config.mode, "strategy": config.strategy if config.mode == "adaptive" else None, "topics": topics,
                "pool_size": len(items), "resume_inventory": inventory[:60]}

    # ================================================================ queries
    def _row(self, c: sqlite3.Connection, iid: int) -> sqlite3.Row:
        row = c.execute("SELECT * FROM interviews WHERE id=?", (iid,)).fetchone()
        if not row:
            raise not_found("Interview")
        return row

    def list(self) -> list[dict[str, Any]]:
        with self.db.read() as c:
            rows = c.execute("""
                SELECT i.id, i.title, i.interview_type, i.status, i.phase, i.created_at, i.completed_at, i.updated_at,
                  (SELECT COUNT(*) FROM interview_items WHERE interview_id=i.id) AS total,
                  (SELECT COUNT(*) FROM interview_items WHERE interview_id=i.id AND status='answered') AS answered,
                  (SELECT COUNT(*) FROM interview_items WHERE interview_id=i.id AND status='skipped') AS skipped,
                  (SELECT COUNT(*) FROM reports WHERE interview_id=i.id) AS has_report,
                  (SELECT data_json FROM reports WHERE interview_id=i.id) AS rep,
                  (SELECT COUNT(*) FROM interview_pool WHERE interview_id=i.id AND status='available') AS pool_left,
                  i.config_json
                FROM interviews i ORDER BY i.created_at DESC, i.id DESC""").fetchall()
        out = []
        for r in rows:
            d = dict(r)
            rep = d.pop("rep")
            pool_left, cfg = d.pop("pool_left"), d.pop("config_json")
            d["average_score"] = (json.loads(rep)["summary"]["average_score"] if rep else None)
            # A running adaptive interview creates its questions one at a time: report the planned total, as get_state does.
            # Finished ones keep the number actually asked.
            d["planned"] = False
            if d["status"] in ACTIVE:
                try:
                    config = InterviewConfig.model_validate_json(cfg)
                except ValueError:
                    config = None
                if config is not None and config.mode == "adaptive":
                    d["total"] = adaptive.planned_total(adaptive.Settings(max_questions=config.max_questions), pool_left, d["total"])
                    d["planned"] = True
            out.append(d)
        return out

    def get_state(self, iid: int) -> dict[str, Any]:
        with self.db.read() as c:
            iv = self._row(c, iid)
            config = InterviewConfig.model_validate_json(iv["config_json"])
            items = [dict(r) for r in c.execute("SELECT * FROM interview_items WHERE interview_id=? ORDER BY position", (iid,))]
            turns = [dict(r) for r in c.execute("SELECT * FROM turns WHERE interview_id=? ORDER BY item_id, seq", (iid,))]
            has_report = bool(c.execute("SELECT 1 FROM reports WHERE interview_id=?", (iid,)).fetchone())
            adaptive_view = self._adaptive_view(c, iv, config, items) if config.mode == "adaptive" else None
            has_next = (self._peek_has_next(c, iv, config, items)
                        if iv["phase"] == "feedback" and iv["status"] in ACTIVE else None)
        scores = _item_scores(turns)
        sealed = config.feedback_mode == "at_end" and iv["status"] in ACTIVE      # scores and feedback stay sealed until the interview ends
        item_views = [{
            "id": it["id"], "position": it["position"], "text": it["text"], "topic": it["topic"],
            "difficulty": it["difficulty"], "status": it["status"], "followup_count": it["followup_count"],
            "source": it.get("source") or "bank", "resume_name": it.get("resume_name"),
            "score": None if sealed else (scores.get(it["id"]) if it["status"] in ("answered", "skipped", "unanswered") else None),
        } for it in items]
        current = None
        next_action = None
        cur_item = next((it for it in items if it["id"] == iv["current_item_id"]), None)
        phase = iv["phase"]
        if cur_item and phase != "done":
            thread_turns = [t for t in turns if t["item_id"] == cur_item["id"]]
            reveal = not sealed and (config.feedback_mode == "immediate" or phase == "feedback")
            pending = next((t for t in thread_turns if t["status"] == "asked"), None)
            if phase == "feedback":
                next_action = "followup" if pending else ("next_question" if has_next else "finish")
            view_turns = []
            for t in thread_turns:
                if t["status"] == "asked" and phase == "feedback":
                    continue  # pending follow-up stays hidden until the candidate presses Continue
                view_turns.append(_turn_view(t, reveal))
            cur_turn = next((t for t in thread_turns if t["id"] == iv["current_turn_id"]), None)
            current = {
                "pending_followup": ({"question": pending["question_text"], "reason": pending["followup_reason"]}
                                     if pending and phase == "feedback" else None),
                "item": {
                    "id": cur_item["id"], "position": cur_item["position"], "text": cur_item["text"],
                    "topic": cur_item["topic"], "difficulty": cur_item["difficulty"],
                    "followup_count": cur_item["followup_count"], "followups_max": config.max_followups,
                    "followups_remaining": max(0, config.max_followups - cur_item["followup_count"]),
                    "source": cur_item.get("source") or "bank", "resume_name": cur_item.get("resume_name"),
                },
                "turn": _turn_view(cur_turn, reveal) if cur_turn and not (phase == "feedback" and cur_turn["status"] == "asked") else None,
                "thread": view_turns,
            }
        done = sum(1 for i in items if i["status"] in ("answered", "skipped", "unanswered"))
        limit_s = config.time_limit_minutes * 60 if config.time_limit_minutes else None
        elapsed = self._elapsed(iv) if iv["status"] in ACTIVE else None
        return {
            "mode": config.mode, "adaptive": adaptive_view, "end_reason": iv["end_reason"],
            "time": {"limit_s": limit_s, "elapsed_s": round(elapsed) if elapsed is not None else None,
                     "remaining_s": max(0, round(limit_s - elapsed)) if limit_s and elapsed is not None else None},
            "id": iv["id"], "title": iv["title"], "interview_type": iv["interview_type"], "status": iv["status"],
            "phase": phase, "error": iv["error"], "config": config.model_dump(),
            "current_turn_id": iv["current_turn_id"],
            "created_at": iv["created_at"], "started_at": iv["started_at"], "completed_at": iv["completed_at"],
            "progress": {
                "total": adaptive_view["planned_total"] if adaptive_view else len(items), "finished": done, "planned": bool(adaptive_view),
                "answered": sum(1 for i in items if i["status"] == "answered"),
                "skipped": sum(1 for i in items if i["status"] == "skipped"),
                "unanswered": sum(1 for i in items if i["status"] == "unanswered"),
                "position": (cur_item["position"] + 1) if cur_item else None,
            },
            "items": item_views, "current": current, "next_action": next_action, "has_report": has_report,
        }

    def _adaptive_view(self, c: sqlite3.Connection, iv, config: InterviewConfig, items: list[dict]) -> dict[str, Any]:
        state = adaptive.EngineState.load(json.loads(iv["adaptive_json"]) if iv["adaptive_json"] else None)
        available = c.execute("SELECT COUNT(*) FROM interview_pool WHERE interview_id=? AND status='available'", (iv["id"],)).fetchone()[0]
        events = [dict(r) for r in c.execute("SELECT kind, decision, reason, item_id, turn_id, level_before, level_after, topic, created_at FROM adaptive_events "
                                              "WHERE interview_id=? ORDER BY id", (iv["id"],))]
        last_select = next((e for e in reversed(events) if e["kind"] == "select"), None)
        return {"strategy": config.strategy, "level": adaptive.LEVELS[state.level], "start_level": config.start_level,
                "target_difficulty": adaptive.LEVEL_DIFFICULTY[adaptive.LEVELS[state.level]], "focus_topic": state.focus_topic,
                "planned_total": adaptive.planned_total(adaptive.Settings(max_questions=config.max_questions), available, len(items)),
                "pool_remaining": available, "current_reason": last_select["reason"] if last_select else None,
                "current_decision": last_select["decision"] if last_select else None,
                "level_history": state.level_history, "events": events[-30:]}

    # ================================================================ commands
    def submit_answer(self, iid: int, body: AnswerIn) -> dict[str, Any]:
        if not body.text:
            raise bad_request("empty_answer", "Type or dictate an answer before submitting.")
        if len(body.text) > MAX_ANSWER_CHARS:
            raise bad_request("answer_too_long", f"Answers are limited to {MAX_ANSWER_CHARS} characters.")
        with self.db.tx() as c:
            self._expect(c, iid, phase="awaiting_answer", turn_id=body.turn_id)   # compare-and-set: raises 409 on a stale or repeated submit
            turn = c.execute("SELECT * FROM turns WHERE id=?", (body.turn_id,)).fetchone()
            if not turn or turn["status"] != "asked":
                raise conflict("already_submitted", "This question was already answered.")
            now = utcnow()
            c.execute("""UPDATE turns SET status='submitted', answer_text=?, answer_source=?, submitted_at=?,
                         eval_attempts=1 WHERE id=?""", (body.text, body.source, now, body.turn_id))
            c.execute("UPDATE interviews SET phase='evaluating', error=NULL, updated_at=? WHERE id=?", (now, iid))
        self.executor.submit(self._evaluate, iid, body.turn_id)
        return self.get_state(iid)

    def retry(self, iid: int, turn_id: int) -> dict[str, Any]:
        with self.db.tx() as c:
            self._expect(c, iid, phase="evaluation_failed", turn_id=turn_id)
            now = utcnow()
            c.execute("UPDATE turns SET eval_attempts=eval_attempts+1 WHERE id=?", (turn_id,))
            c.execute("UPDATE interviews SET phase='evaluating', error=NULL, updated_at=? WHERE id=?", (now, iid))
        self.executor.submit(self._evaluate, iid, turn_id)
        return self.get_state(iid)

    def continue_(self, iid: int, turn_id: int) -> dict[str, Any]:
        finished = False
        with self.db.tx() as c:
            iv = self._expect(c, iid, phase="feedback", turn_id=turn_id)
            turn = c.execute("SELECT * FROM turns WHERE id=?", (turn_id,)).fetchone()
            if turn and turn["status"] == "asked":  # a follow-up is waiting behind the feedback screen
                c.execute("UPDATE interviews SET phase='awaiting_answer', updated_at=? WHERE id=?", (utcnow(), iid))
            else:
                finished = self._advance(c, iv)
        if finished:
            self._after_finish(iid)
        return self.get_state(iid)

    def skip(self, iid: int, turn_id: int) -> dict[str, Any]:
        finished = False
        with self.db.tx() as c:
            iv = self._expect(c, iid, phase=("awaiting_answer", "feedback", "evaluation_failed"), turn_id=turn_id)
            config = InterviewConfig.model_validate_json(iv["config_json"])
            turn = c.execute("SELECT * FROM turns WHERE id=?", (turn_id,)).fetchone()
            if not turn or turn["status"] not in ("asked", "submitted"):
                raise conflict("not_skippable", "There is nothing to skip right now.")
            c.execute("UPDATE turns SET status='skipped' WHERE id=?", (turn_id,))
            if turn["kind"] == "main":
                c.execute("UPDATE interview_items SET status='skipped' WHERE id=?", (turn["item_id"],))
                finished = self._advance(c, iv)
            else:
                c.execute("UPDATE interview_items SET status='answered' WHERE id=?", (turn["item_id"],))
                last = c.execute("""SELECT id FROM turns WHERE item_id=? AND status='evaluated' ORDER BY seq DESC LIMIT 1""",
                                 (turn["item_id"],)).fetchone()
                if config.feedback_mode == "after_followups" and last:
                    c.execute("UPDATE interviews SET phase='feedback', current_turn_id=?, error=NULL, updated_at=? WHERE id=?",
                              (last["id"], utcnow(), iid))
                else:
                    finished = self._advance(c, iv)
        if finished:
            self._after_finish(iid)
        return self.get_state(iid)

    def pause(self, iid: int) -> dict[str, Any]:
        with self.db.tx() as c:
            iv = self._row(c, iid)
            if iv["status"] != "in_progress":
                raise conflict("not_active", "Only a running interview can be paused.")
            now = utcnow()
            c.execute("UPDATE interviews SET status='paused', paused_at=?, updated_at=? WHERE id=?", (now, now, iid))
        self.executor.submit(self._release_model_if_idle)   # queued behind any running evaluation
        return self.get_state(iid)

    def resume(self, iid: int) -> dict[str, Any]:
        with self.db.tx() as c:
            iv = self._row(c, iid)
            if iv["status"] != "paused":
                raise conflict("not_paused", "This interview is not paused.")
            paused = _seconds_between(iv["paused_at"], utcnow())
            c.execute("UPDATE interviews SET status='in_progress', paused_at=NULL, paused_seconds=paused_seconds+?, updated_at=? WHERE id=?",
                      (paused, utcnow(), iid))
        return self.get_state(iid)

    def end(self, iid: int) -> dict[str, Any]:
        with self.db.tx() as c:
            iv = self._row(c, iid)
            if iv["status"] not in ACTIVE:
                raise conflict("not_active", "This interview has already finished.")
            if iv["phase"] == "evaluating":
                raise conflict("evaluating", "Wait for the current evaluation to finish before ending the interview.")
            c.execute("UPDATE interviews SET end_reason='ended_by_user' WHERE id=?", (iid,))
            self._finish(c, iv, "ended")
        self._after_finish(iid)
        return self.get_state(iid)

    def delete(self, iid: int) -> None:
        with self.db.tx() as c:
            iv = self._row(c, iid)
            if iv["phase"] == "evaluating":
                raise conflict("evaluating", "Wait for the current evaluation to finish before deleting.")
            c.execute("DELETE FROM interviews WHERE id=?", (iid,))

    def clear_all(self) -> int:
        with self.db.tx() as c:
            if c.execute("SELECT 1 FROM interviews WHERE phase='evaluating'").fetchone():
                raise conflict("evaluating", "An evaluation is still running; try again in a moment.")
            return c.execute("DELETE FROM interviews").rowcount

    # ================================================================ internals
    def _expect(self, c: sqlite3.Connection, iid: int, *, phase, turn_id: int) -> sqlite3.Row:
        iv = self._row(c, iid)
        if iv["status"] == "paused":
            raise conflict("paused", "The interview is paused. Resume it first.")
        if iv["status"] != "in_progress":
            raise conflict("finished", "This interview has finished.")
        phases = (phase,) if isinstance(phase, str) else phase
        if iv["phase"] not in phases:
            raise conflict("wrong_phase", f"Not possible right now (state: {iv['phase']}).", phase=iv["phase"])
        if iv["current_turn_id"] != turn_id:
            raise conflict("stale_turn", "That question is no longer current. The page was out of date.")
        return iv

    def _activate_next(self, c: sqlite3.Connection, iv: sqlite3.Row, finished_one: bool = False) -> bool:
        """Make the next item active and ask its question. Returns False if the interview should end.

        Fixed mode: the next pending item in order. Adaptive mode: the engine chooses from the pool (decision persisted)."""
        config = InterviewConfig.model_validate_json(iv["config_json"])
        if config.mode == "adaptive":
            nxt = self._adaptive_pick(c, iv, config, finished_one)
        else:
            if config.time_limit_minutes and self._elapsed(iv) >= config.time_limit_minutes * 60:
                c.execute("UPDATE interviews SET end_reason='time_limit' WHERE id=?", (iv["id"],))
                return False
            nxt = c.execute("SELECT * FROM interview_items WHERE interview_id=? AND status='pending' ORDER BY position LIMIT 1",
                            (iv["id"],)).fetchone()
        if not nxt:
            return False
        now = utcnow()
        c.execute("UPDATE interview_items SET status='active' WHERE id=?", (nxt["id"],))
        cur = c.execute("""INSERT INTO turns(interview_id, item_id, seq, kind, question_text, status, asked_at)
                           VALUES (?,?,0,'main',?, 'asked', ?)""", (iv["id"], nxt["id"], nxt["text"], now))
        c.execute("""UPDATE interviews SET current_item_id=?, current_turn_id=?, phase='awaiting_answer', error=NULL,
                     updated_at=? WHERE id=?""", (nxt["id"], cur.lastrowid, now, iv["id"]))
        return True

    def _advance(self, c: sqlite3.Connection, iv: sqlite3.Row) -> bool:
        """Move to the next question; returns True when the interview just completed."""
        if self._activate_next(c, self._row(c, iv["id"]), finished_one=True):
            return False
        self._finish(c, iv, "completed")
        return True

    # ---------------------------------------------------------------- adaptive engine glue
    @staticmethod
    def _elapsed(iv) -> float:
        """Active interview time in seconds: wall time since start minus paused time (including a pause in progress)."""
        now = utcnow()
        total = _seconds_between(iv["started_at"] or iv["created_at"], now)
        paused = (iv["paused_seconds"] or 0) + (_seconds_between(iv["paused_at"], now) if iv["paused_at"] else 0)
        return max(0.0, total - paused)

    def _engine_inputs(self, c: sqlite3.Connection, iv, config: InterviewConfig):
        pool_rows = c.execute("SELECT * FROM interview_pool WHERE interview_id=? AND status='available' ORDER BY ord", (iv["id"],)).fetchall()
        items = [dict(r) for r in c.execute("SELECT * FROM interview_items WHERE interview_id=? ORDER BY position", (iv["id"],))]
        turns = [dict(r) for r in c.execute("SELECT * FROM turns WHERE interview_id=? ORDER BY item_id, seq", (iv["id"],))]
        scores = _item_scores(turns)
        history = []
        for it in items:
            main = next((t for t in turns if t["item_id"] == it["id"] and t["kind"] == "main"), None)
            conf = "medium"
            if main and main["evaluation_json"]:
                conf = json.loads(main["evaluation_json"]).get("confidence") or "medium"
            claim = _claim(it)
            history.append(adaptive.Asked(text=it["text"], topic=it["topic"], difficulty=it["difficulty"],
                                          status=it["status"] if it["status"] in ("answered", "skipped", "unanswered") else "active",
                                          score=scores.get(it["id"]), confidence=conf, source=it.get("source") or "bank",
                                          claim_label=(claim or {}).get("label")))
        pool = [adaptive.PoolQ(id=r["id"], order=r["ord"], text=r["text"], topic=r["topic"], difficulty=r["difficulty"], source=r["source"],
                               claim_label=(_claim(r) or {}).get("label")) for r in pool_rows]
        settings = adaptive.Settings(strategy=config.strategy, max_questions=config.max_questions,
                                     time_limit_s=config.time_limit_minutes * 60 if config.time_limit_minutes else None, focus_topic=config.focus_topic)
        return pool_rows, pool, history, settings

    def _adaptive_pick(self, c: sqlite3.Connection, iv, config: InterviewConfig, finished_one: bool):
        """Ask the engine for the next question; persist its state and decision; turn the chosen pool question into an item."""
        pool_rows, pool, history, settings = self._engine_inputs(c, iv, config)
        state = adaptive.EngineState.load(json.loads(iv["adaptive_json"]) if iv["adaptive_json"] else None)
        if finished_one:
            state = adaptive.record_finished(state)
        decision, state = adaptive.decide_next(pool=pool, history=history, state=state, settings=settings, elapsed_s=self._elapsed(iv))
        now = utcnow()
        c.execute("UPDATE interviews SET adaptive_json=? WHERE id=?", (json.dumps(state.dump()), iv["id"]))
        if decision.action == "end":
            c.execute("UPDATE interviews SET end_reason=? WHERE id=?", (decision.kind, iv["id"]))
            self._event(c, iv["id"], "end", decision.kind, decision.reason, level_before=decision.level_before, level_after=decision.level_after)
            return None
        row = next(r for r in pool_rows if r["id"] == decision.pool_id)
        pos = c.execute("SELECT COALESCE(MAX(position)+1, 0) FROM interview_items WHERE interview_id=?", (iv["id"],)).fetchone()[0]
        item_id = c.execute("""INSERT INTO interview_items(interview_id, position, question_id, text, rubric, topic, difficulty, status, created_at,
                               source, resume_id, resume_name, claim_json) VALUES (?,?,?,?,?,?,?,'pending',?,?,?,?,?)""",
                            (iv["id"], pos, row["question_id"], row["text"], row["rubric"], row["topic"], row["difficulty"], now, row["source"],
                             row["resume_id"], row["resume_name"], row["claim_json"])).lastrowid
        c.execute("UPDATE interview_pool SET status='used', item_id=? WHERE id=?", (item_id, row["id"]))
        self._event(c, iv["id"], "select", decision.kind, decision.reason, item_id=item_id, level_before=decision.level_before,
                    level_after=decision.level_after, topic=decision.topic)
        return c.execute("SELECT * FROM interview_items WHERE id=?", (item_id,)).fetchone()

    @staticmethod
    def _event(c: sqlite3.Connection, iid: int, kind: str, decision: str, reason: str, *, item_id=None, turn_id=None, level_before=None,
               level_after=None, topic=None) -> None:
        c.execute("""INSERT INTO adaptive_events(interview_id, kind, decision, reason, item_id, turn_id, level_before, level_after, topic, created_at)
                     VALUES (?,?,?,?,?,?,?,?,?,?)""", (iid, kind, decision, reason[:500], item_id, turn_id, level_before, level_after, topic, utcnow()))

    def _peek_has_next(self, c: sqlite3.Connection, iv, config: InterviewConfig, items: list[dict]) -> bool:
        """Would another question follow? Fixed: any pending item. Adaptive: the engine's (side-effect free) decision."""
        if config.mode != "adaptive":
            if config.time_limit_minutes and self._elapsed(iv) >= config.time_limit_minutes * 60:
                return False
            return any(i["status"] == "pending" for i in items)
        _, pool, history, settings = self._engine_inputs(c, iv, config)
        state = adaptive.record_finished(adaptive.EngineState.load(json.loads(iv["adaptive_json"]) if iv["adaptive_json"] else None))
        history = [h if h.status != "active" else adaptive.Asked(**{**h.__dict__, "status": "answered"}) for h in history]
        decision, _ = adaptive.decide_next(pool=pool, history=history, state=state, settings=settings, elapsed_s=self._elapsed(iv))
        return decision.action == "ask"

    def _finish(self, c: sqlite3.Connection, iv: sqlite3.Row, status: str) -> None:
        iid = iv["id"]
        for it in c.execute("SELECT * FROM interview_items WHERE interview_id=? AND status IN ('pending','active')", (iid,)).fetchall():
            has_answer = c.execute("SELECT 1 FROM turns WHERE item_id=? AND status IN ('submitted','evaluated')", (it["id"],)).fetchone()
            c.execute("UPDATE interview_items SET status=? WHERE id=?", ("answered" if has_answer else "unanswered", it["id"]))
        now = utcnow()
        c.execute("""UPDATE interviews SET status=?, phase='done', current_turn_id=NULL, error=NULL, completed_at=?,
                     end_reason=COALESCE(end_reason, ?), updated_at=? WHERE id=?""", (status, now, "all_questions" if status == "completed" else "ended_by_user", now, iid))
        reports.store_report(c, iid)

    def _after_finish(self, iid: int) -> None:
        self.executor.submit(self._generate_narrative, iid)

    # ---------------------------------------------------------------- evaluation worker
    def _evaluate(self, iid: int, turn_id: int) -> None:
        try:
            with self.db.read() as c:
                iv = self._row(c, iid)
                if iv["phase"] != "evaluating" or iv["current_turn_id"] != turn_id:
                    return  # obsolete request
                turn = c.execute("SELECT * FROM turns WHERE id=?", (turn_id,)).fetchone()
                item = c.execute("SELECT * FROM interview_items WHERE id=?", (turn["item_id"],)).fetchone()
                prior = c.execute("SELECT * FROM turns WHERE item_id=? AND status='evaluated' AND seq<? ORDER BY seq",
                                  (item["id"], turn["seq"])).fetchall()
            config = InterviewConfig.model_validate_json(iv["config_json"])
            thread = []
            for p in prior:
                ev = json.loads(p["evaluation_json"] or "{}")
                thread.append({"question": p["question_text"], "answer": p["answer_text"] or "",
                               "missing": ev.get("missing_concepts", []), "misconceptions": ev.get("misconceptions", [])})
            said = turn["answer_text"] or ""
            interpreted: Optional[str] = None
            label = f"Q{item['position'] + 1}" + (" follow-up" if turn["kind"] == "followup" else "")
            if (turn["answer_source"] or "typed") == "voice" and said.strip():   # repair speech-recognition garble before grading
                with usage_context(iid, label):
                    fixed = self.evaluator.interpret_transcript(turn["question_text"], said)
                interpreted = fixed if fixed.strip() != said.strip() else None
            ctx = EvalContext(
                question=item["text"], rubric=item["rubric"], topic=item["topic"], difficulty=item["difficulty"],
                interview_type=iv["interview_type"], strictness=config.strictness, current_question=turn["question_text"],
                current_kind=turn["kind"], answer=interpreted or said, thread=thread,
                followups_remaining=max(0, config.max_followups - item["followup_count"]),
                answer_source=turn["answer_source"] or "typed",
                claim=_claim(item),
                profile_key=eval_profiles.detect_category(topic=item["topic"], text=item["text"], interview_type=iv["interview_type"]),
            )
            with usage_context(iid, label):
                raw = self.evaluator.evaluate(ctx, self.questions.get_rubric())
                self._polish_followup(raw, item=item, turn=turn, config=config, prior=prior, answer=interpreted or said)
        except LLMError as e:
            self._fail(iid, turn_id, e.message)
            return
        except AppError:
            return
        except Exception as e:  # never leave the interview stuck in 'evaluating'
            log.exception("unexpected evaluation failure")
            self._fail(iid, turn_id, f"Unexpected error during evaluation ({type(e).__name__}).")
            return
        try:
            self._apply(iid, turn_id, raw, interpreted, profile_key=ctx.profile_key, input_hash=getattr(self.evaluator, "last_input_hash", None))
        except Exception as e:
            log.exception("failed to apply evaluation")
            self._fail(iid, turn_id, f"Could not save the evaluation ({type(e).__name__}).")

    def _fail(self, iid: int, turn_id: int, message: str) -> None:
        log.warning("evaluation failed for interview %s: %s", iid, message)
        with self.db.tx() as c:
            c.execute("""UPDATE interviews SET phase='evaluation_failed', error=?, updated_at=?
                         WHERE id=? AND phase='evaluating' AND current_turn_id=?""", (message, utcnow(), iid, turn_id))

    def _apply(self, iid: int, turn_id: int, raw: LLMEvaluation, interpreted: Optional[str] = None, *, profile_key: str = "general",
               input_hash: Optional[str] = None) -> None:
        finished = False
        with self.db.tx() as c:
            iv = self._row(c, iid)
            turn = c.execute("SELECT * FROM turns WHERE id=?", (turn_id,)).fetchone()
            if iv["phase"] != "evaluating" or iv["current_turn_id"] != turn_id or turn["status"] != "submitted":
                return  # superseded (e.g. interview deleted/ended): drop the stale result
            config = InterviewConfig.model_validate_json(iv["config_json"])
            item = c.execute("SELECT * FROM interview_items WHERE id=?", (turn["item_id"],)).fetchone()
            previous = [item["text"]] + [r["question_text"] for r in c.execute("SELECT question_text FROM turns WHERE item_id=?", (item["id"],))]
            rubric = self.questions.get_rubric()
            answer_text = turn["answer_text"] or ""
            kind = None
            if config.mode == "adaptive":
                decision, kind = self._adaptive_followup(c, iv, config, item, turn, raw, rubric, interpreted, profile_key, previous)
            else:                             # fixed interviews keep the v1 follow-up policy exactly
                decision = decide_followup(raw, max_followups=config.max_followups, used_followups=item["followup_count"],
                                           previous_questions=previous, answer=answer_text)
            final = self.evaluator.finalize(raw, rubric, decision, difficulty=item["difficulty"] if item else None,
                                            interpreted_answer=interpreted, answer=answer_text, profile_key=profile_key,
                                            input_hash=input_hash, followup_kind=kind)
            now = utcnow()
            c.execute("UPDATE turns SET status='evaluated', evaluation_json=?, score=?, evaluated_at=? WHERE id=?",
                      (final.model_dump_json(), final.score, now, turn_id))
            if decision.ask:
                used = c.execute("SELECT COUNT(*) FROM turns WHERE item_id=? AND kind='followup'", (item["id"],)).fetchone()[0]
                assert used < config.max_followups, "follow-up limit would be exceeded"  # belt and braces
                seq = c.execute("SELECT MAX(seq)+1 FROM turns WHERE item_id=?", (item["id"],)).fetchone()[0]
                cur = c.execute("""INSERT INTO turns(interview_id, item_id, seq, kind, question_text, followup_reason, status, asked_at)
                                   VALUES (?,?,?,'followup',?,?, 'asked', ?)""",
                                (iid, item["id"], seq, decision.question, decision.reason, now))
                c.execute("UPDATE interview_items SET followup_count=followup_count+1 WHERE id=?", (item["id"],))
                if config.mode == "adaptive":
                    self._event(c, iid, "followup", kind or "probe_gap", decision.reason or "Follow-up on the answer.", item_id=item["id"],
                                turn_id=cur.lastrowid, topic=item["topic"])
                phase = "feedback" if config.feedback_mode == "immediate" else "awaiting_answer"
                c.execute("UPDATE interviews SET phase=?, current_turn_id=?, error=NULL, updated_at=? WHERE id=?",
                          (phase, cur.lastrowid, now, iid))
            else:
                c.execute("UPDATE interview_items SET status='answered' WHERE id=?", (item["id"],))
                if config.feedback_mode == "at_end":      # nothing to show now: straight on to the next question (or the end)
                    finished = self._advance(c, iv)
                else:
                    c.execute("UPDATE interviews SET phase='feedback', error=NULL, updated_at=? WHERE id=?", (now, iid))
        if finished:
            self._after_finish(iid)

    def _adaptive_followup(self, c, iv, config: InterviewConfig, item, turn, raw: LLMEvaluation, rubric, interpreted, profile_key: str,
                           previous: list[str]) -> tuple[FollowUpDecision, Optional[str]]:
        """Adaptive follow-up: the same hard limits as fixed interviews, plus clarify / deepen / scenario choices and a loop guard."""
        answer = turn["answer_text"] or ""
        g = self.evaluator.assess(raw, answer=answer, interpreted_answer=interpreted)
        level = question_level(raw.question_level, item["difficulty"])
        prelim = eval_profiles.score_answer(g.dimension_scores, eval_profiles.get_profile(profile_key), rubric, level, raw.production_relevant).score
        earlier = [r["score"] for r in c.execute("SELECT score FROM turns WHERE item_id=? AND status='evaluated' AND score IS NOT NULL ORDER BY seq", (item["id"],))]
        state = adaptive.EngineState.load(json.loads(iv["adaptive_json"]) if iv["adaptive_json"] else None)
        choice = adaptive.choose_followup(
            gap_question=raw.followup_question if raw.needs_followup else "", gap_reason=raw.followup_reason,
            deeper_question=raw.deeper_question, score=prelim, classification=g.classification, confidence=g.confidence,
            practical_score=g.dimension_scores.practical_application, strategy=config.strategy, level=adaptive.LEVELS[state.level],
            used=item["followup_count"], max_followups=config.max_followups, previous_scores=earlier,
            is_followup_turn=turn["kind"] == "followup", non_attempt=is_non_attempt(answer),
            too_similar=lambda q: too_similar(q, previous))
        return FollowUpDecision(choice.ask, question=choice.question, reason=choice.reason, suppressed_reason=choice.suppressed_reason), choice.kind

    def _polish_followup(self, raw: LLMEvaluation, *, item, turn, config, prior, answer: str) -> None:
        """Cloud mode: a dedicated conversation model writes the follow-up question (one small extra call, only when one will really be asked).
        Any failure keeps the grader's own draft; this step can never make an evaluation fail."""
        if not (self.evaluator.writes_followups_separately() and raw.needs_followup):
            return
        if config.max_followups <= item["followup_count"] or is_non_attempt(answer):
            return
        gap = next(iter([*raw.missing_concepts, *raw.misconceptions]), "")
        if not gap:
            return
        earlier = [item["text"], *[p["question_text"] for p in prior], turn["question_text"]]
        better = self.evaluator.generate_followup(question=item["text"], answer=answer, gap=gap, draft=raw.followup_question, earlier=earlier, claim=_claim(item))
        if better:
            raw.followup_question = better

    # ---------------------------------------------------------------- memory
    def _release_model_if_idle(self) -> None:
        """Hand the model's ~4 GB back to the computer as soon as no interview is running, instead of after the keep-alive timer.
        Otherwise the rest of the machine stays slow (swapping) for minutes after practice is over."""
        settings = self.evaluator.ollama.settings
        if not settings.llm_unload_when_idle:
            return
        try:
            with self.db.read() as c:
                running = c.execute("SELECT 1 FROM interviews WHERE status='in_progress' LIMIT 1").fetchone()
            if not running and not any(check() for check in self.busy_checks):
                self.evaluator.ollama.unload(settings.llm_model)
        except Exception:
            log.exception("could not release the model")

    # ---------------------------------------------------------------- report narrative
    def _generate_narrative(self, iid: int) -> None:
        try:
            with usage_context(iid, "Report summary"):
                self._generate_narrative_inner(iid)
        finally:
            self._release_model_if_idle()   # the summary was the last use of the model for this interview

    def _generate_narrative_inner(self, iid: int) -> None:
        try:
            with self.db.read() as c:
                row = c.execute("SELECT data_json FROM reports WHERE interview_id=?", (iid,)).fetchone()
            if not row:
                return
            data = json.loads(row["data_json"])
            digest = reports.narrative_digest(data)
            if digest is None:  # nothing was evaluated; the rule-based text is all there is
                reports.set_narrative(self.db, iid, None, "ready", None)
                return
            narrative = self.evaluator.narrative(digest)
            reports.set_narrative(self.db, iid, narrative.model_dump(), "ready", None)
        except LLMError as e:
            reports.set_narrative(self.db, iid, None, "failed", e.message)
        except Exception as e:
            log.exception("narrative generation failed")
            reports.set_narrative(self.db, iid, None, "failed", f"Unexpected error ({type(e).__name__}).")

    def regenerate_narrative(self, iid: int) -> dict[str, Any]:
        with self.db.tx() as c:
            row = c.execute("SELECT narrative_status FROM reports WHERE interview_id=?", (iid,)).fetchone()
            if not row:
                raise not_found("Report")
            if row["narrative_status"] == "pending":
                raise conflict("pending", "A summary is already being generated.")
            c.execute("UPDATE reports SET narrative_status='pending', narrative_error=NULL, updated_at=? WHERE interview_id=?",
                      (utcnow(), iid))
        self.executor.submit(self._generate_narrative, iid)
        return reports.get_report(self.db, iid)


# ---------------------------------------------------------------------- helpers
def mix_items(bank: list[dict[str, Any]], resume: list[dict[str, Any]], mix: str) -> list[dict[str, Any]]:
    """Order bank and resume questions. interleave alternates (resume first) and appends the remainder; shuffled mixes everything."""
    if mix == "resume_first":
        return resume + bank
    if mix == "interleave":
        out: list[dict[str, Any]] = []
        for i in range(max(len(bank), len(resume))):
            if i < len(resume):
                out.append(resume[i])
            if i < len(bank):
                out.append(bank[i])
        return out
    if mix == "shuffled":
        out = bank + resume
        random.SystemRandom().shuffle(out)
        return out
    return bank + resume


def _seconds_between(a: Optional[str], b: Optional[str]) -> float:
    if not a or not b:
        return 0.0
    try:
        return max(0.0, (datetime.fromisoformat(b) - datetime.fromisoformat(a)).total_seconds())
    except ValueError:
        return 0.0


def _claim(item) -> Optional[dict[str, Any]]:
    """The resume claim a resume-sourced question is about (None for question-bank items)."""
    keys = item.keys() if hasattr(item, "keys") else []
    if "source" not in keys or item["source"] != "resume" or not item["claim_json"]:
        return None
    try:
        claim = json.loads(item["claim_json"])
    except ValueError:
        return None
    return claim if isinstance(claim, dict) else None


def _turn_view(t: Optional[dict], reveal: bool) -> Optional[dict[str, Any]]:
    if t is None:
        return None
    view = {
        "id": t["id"], "seq": t["seq"], "kind": t["kind"], "question_text": t["question_text"], "status": t["status"],
        "answer_text": t["answer_text"], "answer_source": t["answer_source"],
        "followup_reason": t["followup_reason"], "eval_attempts": t["eval_attempts"],
    }
    if t["status"] == "evaluated" and reveal:
        ev = json.loads(t["evaluation_json"])
        ev.pop("followup_question", None)  # the follow-up is shown as its own turn, when it is due
        view["evaluation"] = ev
        view["score"] = t["score"]
    return view


def _item_scores(turns: list[dict]) -> dict[int, float]:
    by_item: dict[int, list[dict]] = {}
    for t in turns:
        by_item.setdefault(t["item_id"], []).append(t)
    out = {}
    for iid, ts in by_item.items():
        s = reports.item_score(ts)
        if s is not None:
            out[iid] = s
    return out
