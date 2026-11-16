"""Adaptive interviews through the API: lifecycle, persistence, recovery, safeguards, time limits and the report."""
import json
import sqlite3

from fastapi.testclient import TestClient

from app.db import SCHEMA, Database, _split_statements
from app.deps import build_container
from app.main import create_app
from conftest import InlineExecutor, act, answer, make_client_for, make_settings, state
from intel_fixtures import graded, ready_resume

BANK = [("What is a primary key?", "SQL", "easy"), ("Explain INNER versus LEFT JOIN.", "SQL", "medium"),
        ("How would you fix a slow query scanning 500M rows?", "SQL", "hard"), ("What is a list comprehension?", "Python", "easy"),
        ("Explain how generators save memory.", "Python", "medium"), ("Design a retry decorator with backoff and jitter.", "Python", "hard")]


def bank(client, set_id):
    for text, topic, diff in BANK:
        assert client.post(f"/api/sets/{set_id}/questions", json={"text": text, "topic": topic, "difficulty": diff}).status_code == 201


def start(client, set_id, **cfg):
    body = {"set_id": set_id, "config": {"title": "Adaptive", "mode": "adaptive", "feedback_mode": "at_end", "max_followups": 0, **cfg}}
    extra = cfg.pop("_body", None)
    r = client.post("/api/interviews", json={**body, **(extra or {})})
    assert r.status_code == 201, r.text
    return r.json()


def test_adaptive_interview_picks_from_the_pool_and_records_why(client, set_id, fake):
    bank(client, set_id)
    st = start(client, set_id, start_level="beginner", max_questions=4)
    assert st["mode"] == "adaptive" and st["progress"]["planned"] and st["progress"]["total"] == 4
    assert len(st["items"]) == 1 and st["items"][0]["difficulty"] == "easy"           # only the chosen question becomes an item
    ad = st["adaptive"]
    assert ad["level"] == "beginner" and ad["current_decision"] == "start" and ad["current_reason"] and ad["pool_remaining"] == 5
    fake.chat_replies = [graded(9), graded(9), graded(9), graded(9)]
    for _ in range(4):
        st = answer(client, st, "A clear and correct explanation of the idea").json()
    assert st["status"] == "completed" and st["end_reason"] == "end_max"
    rep = client.get(f"/api/interviews/{st['id']}/report").json()
    assert rep["summary"]["total_questions"] == 4                                        # unasked pool questions are not "unanswered"
    assert rep["adaptive"]["final_level"] in ("intermediate", "advanced") and rep["adaptive"]["level_history"]
    assert [e["kind"] for e in rep["adaptive"]["events"]][-1] == "end"
    assert rep["adaptive"]["pool_unused"] == 2


def test_difficulty_drops_after_weak_answers(client, set_id, fake):
    bank(client, set_id)
    st = start(client, set_id, start_level="advanced", max_questions=4)
    assert st["items"][0]["difficulty"] == "hard"
    fake.chat_replies = [graded(2), graded(2), graded(5), graded(5)]
    st = answer(client, st, "Maybe add an index on the filter column").json()
    st = answer(client, st, "Something about memory").json()
    assert st["adaptive"]["level"] == "intermediate" and "easier" in st["adaptive"]["current_reason"]
    assert st["items"][-1]["difficulty"] == "medium"


def test_skipped_questions_are_not_scored_and_can_lower_difficulty(client, set_id, fake):
    bank(client, set_id)
    st = start(client, set_id, start_level="advanced", max_questions=5)
    st = act(client, st, "skip").json()
    st = act(client, st, "skip").json()
    assert st["adaptive"]["level"] == "intermediate"
    assert [i["score"] for i in st["items"] if i["status"] == "skipped"] == [None, None]
    assert not fake.chat_calls


def test_duplicate_submission_runs_one_evaluation(client, set_id, fake):
    bank(client, set_id)
    st = start(client, set_id, max_questions=3, feedback_mode="immediate")
    fake.chat_replies = [graded(7)]
    assert answer(client, st, "first").status_code == 200
    again = answer(client, st, "first")
    assert again.status_code == 409 and len(fake.chat_calls) == 1


def test_failed_model_call_keeps_the_answer_and_retry_continues(client, set_id, fake):
    bank(client, set_id)
    st = start(client, set_id, max_questions=3)
    fake.chat_error = (500, "boom")
    st = answer(client, st, "My kept answer").json()
    assert st["phase"] == "evaluation_failed" and st["current"]["turn"]["answer_text"] == "My kept answer"
    fake.chat_error = None
    fake.chat_replies = [graded(7)]
    st = act(client, st, "retry").json()
    assert st["phase"] == "awaiting_answer" and len(st["items"]) == 2


def test_invalid_model_output_twice_fails_safely(client, set_id, fake):
    bank(client, set_id)
    st = start(client, set_id, max_questions=3)
    fake.chat_replies = ["not json", "{still not json"]
    st = answer(client, st, "An answer").json()
    assert st["phase"] == "evaluation_failed" and "Retry" in st["error"]


def test_state_survives_a_restart_and_interrupted_evaluation_recovers(tmp_path, fake):
    settings = make_settings(tmp_path)
    c1 = build_container(settings, ollama=make_client_for(settings, fake), executor=InlineExecutor())
    client = TestClient(create_app(settings, c1), base_url="http://127.0.0.1:3000")
    sid = client.get("/api/sets").json()[0]["id"]
    bank(client, sid)
    st = start(client, sid, max_questions=4, start_level="beginner")
    fake.chat_replies = [graded(9)]
    st = answer(client, st, "answer one").json()
    first_two = [i["text"] for i in st["items"]]
    with c1.db.tx() as c:                       # simulate a crash in the middle of an evaluation
        c.execute("UPDATE interviews SET phase='evaluating'")
    c2 = build_container(settings, ollama=make_client_for(settings, fake), executor=InlineExecutor())
    client2 = TestClient(create_app(settings, c2), base_url="http://127.0.0.1:3000")
    st2 = state(client2, st["id"])
    assert st2["phase"] == "evaluation_failed" and [i["text"] for i in st2["items"]] == first_two
    assert st2["adaptive"]["pool_remaining"] == 4 and st2["adaptive"]["level"] == "beginner"


def test_time_limit_ends_after_the_current_question(client, container, set_id, fake):
    bank(client, set_id)
    st = start(client, set_id, max_questions=6, time_limit_minutes=5)
    assert st["time"]["limit_s"] == 300 and 0 <= st["time"]["remaining_s"] <= 300
    with container.db.tx() as c:
        c.execute("UPDATE interviews SET started_at='2000-01-01T00:00:00+00:00'")
    fake.chat_replies = [graded(7)]
    st = answer(client, st, "An answer given after the limit").json()
    assert st["status"] == "completed" and st["end_reason"] == "end_time"
    assert st["progress"]["answered"] == 1                                               # the answer in progress was still accepted


def test_paused_time_does_not_count(client, container, set_id):
    bank(client, set_id)
    st = start(client, set_id, max_questions=6, time_limit_minutes=5)
    act(client, st, "pause")
    with container.db.tx() as c:
        c.execute("UPDATE interviews SET started_at='2000-01-01T00:00:00+00:00', paused_at='2000-01-01T00:00:10+00:00'")
    st = client.post(f"/api/interviews/{st['id']}/resume").json()
    assert st["time"]["elapsed_s"] <= 15


def test_fixed_mode_respects_a_time_limit_too(client, container, set_id, fake):
    bank(client, set_id)
    r = client.post("/api/interviews", json={"set_id": set_id, "config": {"feedback_mode": "at_end", "max_followups": 0, "time_limit_minutes": 10}})
    st = r.json()
    assert st["mode"] == "fixed" and st["adaptive"] is None and len(st["items"]) == 6
    with container.db.tx() as c:
        c.execute("UPDATE interviews SET started_at='2000-01-01T00:00:00+00:00'")
    fake.chat_replies = [graded(7)]
    st = answer(client, st, "An answer").json()
    assert st["status"] == "completed" and st["end_reason"] == "time_limit" and st["progress"]["unanswered"] == 5


def test_adaptive_followups_are_decided_and_logged(client, set_id, fake):
    bank(client, set_id)
    st = start(client, set_id, max_questions=2, max_followups=2, feedback_mode="immediate")
    fake.chat_replies = [graded(5, followup="What happens to NULL keys in that join?", missing=["NULL handling"]), graded(5, followup="And with duplicate keys on both sides?")]
    st = answer(client, st, "It keeps rows from one side").json()
    assert st["next_action"] == "followup"
    ev = st["current"]["thread"][0]["evaluation"]
    assert ev["followup_kind"] == "probe_gap" and ev["profile"] == "sql"
    st = act(client, st, "continue").json()
    st = answer(client, st, "They get matched").json()                                   # same score again: the loop guard stops probing
    assert st["next_action"] in ("next_question", "finish")
    events = st["adaptive"]["events"]
    assert any(e["kind"] == "followup" and e["decision"] == "probe_gap" for e in events)


def test_resume_strategy_needs_resume_questions(client, set_id):
    bank(client, set_id)
    r = client.post("/api/interviews", json={"set_id": set_id, "config": {"mode": "adaptive", "strategy": "resume"}})
    assert r.status_code == 400 and r.json()["error"]["code"] == "no_resume_questions"


def test_resume_to_adaptive_interview_end_to_end(client, container, set_id, fake):
    """Upload (ready resume) -> profile -> personalised plan -> adaptive questions about real claims -> report with coverage."""
    rid = ready_resume(container)
    r = client.post("/api/interviews", json={"set_id": None, "config": {"mode": "adaptive", "strategy": "resume", "max_questions": 3,
                                                                        "include_bank": False, "feedback_mode": "at_end", "max_followups": 0},
                                             "resume_auto": {"resume_id": rid, "count": 6}})
    assert r.status_code == 201, r.text
    st = r.json()
    assert st["items"][0]["source"] == "resume" and st["items"][0]["resume_name"] == "Resume 1"
    fake.chat_replies = [graded(7), graded(4), graded(8)]
    for _ in range(3):
        st = answer(client, st, "I owned the pipeline design and the retry policy").json()
    rep = client.get(f"/api/interviews/{st['id']}/report").json()
    claims = [q["claim"] for q in rep["questions"]]
    assert all(c and c["excerpt"] for c in claims)                                       # every question is traceable to a resume statement
    with container.db.read() as c:
        raw = c.execute("SELECT raw_text FROM resumes WHERE id=?", (rid,)).fetchone()[0]
    assert all(c["label"].split(" at ")[0].split(":")[0] in raw or c["label"] in raw for c in claims)
    cov = rep["resume_coverage"]
    assert cov["claims_total"] == 3 and 1 <= cov["claims_discussed"] <= 3
    prompt = fake.chat_calls[0]["messages"][1]["content"]
    assert "<<<RESUME_CLAIM" in prompt                                                   # graded as a resume question, claim fenced as untrusted


def test_v5_database_upgrades_to_v6_and_old_interviews_still_load(tmp_path, fake):
    path = tmp_path / "data" / "interviewer.sqlite3"
    path.parent.mkdir(parents=True)
    raw = sqlite3.connect(path)
    for stmt in _split_statements(SCHEMA):                  # SCHEMA is the v5 definition
        raw.execute(stmt)
    now = "2026-10-01T10:00:00+00:00"
    raw.execute("INSERT INTO question_sets(name, created_at, updated_at) VALUES ('Old', ?, ?)", (now, now))
    raw.execute("INSERT INTO interviews(set_id, title, interview_type, status, phase, config_json, created_at, updated_at) VALUES (1,'Old run','technical','completed','done',?,?,?)",
                (json.dumps({"title": "Old run"}), now, now))
    raw.execute("INSERT INTO interview_items(interview_id, position, text, status, created_at) VALUES (1, 0, 'Old question?', 'answered', ?)", (now,))
    raw.execute("PRAGMA user_version=5")
    raw.commit()
    raw.close()
    settings = make_settings(tmp_path)
    c = build_container(settings, ollama=make_client_for(settings, fake), executor=InlineExecutor())
    with c.db.read() as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 6
        assert conn.execute("SELECT title, paused_seconds, end_reason FROM interviews").fetchone()[:] == ("Old run", 0, None)
        assert conn.execute("SELECT COUNT(*) FROM interview_pool").fetchone()[0] == 0
    client = TestClient(create_app(settings, c), base_url="http://127.0.0.1:3000")
    st = state(client, 1)
    assert st["mode"] == "fixed" and st["adaptive"] is None and st["items"][0]["text"] == "Old question?"
    assert Database(path)                                     # re-opening an up-to-date database is a no-op


def test_untagged_or_single_topic_pool_runs_to_its_question_limit(client, set_id, fake):
    for w in ["caching", "sharding", "hashing", "queues", "retries", "logging", "tracing", "batching"]:
        client.post(f"/api/sets/{set_id}/questions", json={"text": f"When would you use {w} in a backend?"})
    st = start(client, set_id, max_questions=6)
    fake.chat_replies = [graded(8) for _ in range(6)]
    for _ in range(6):
        st = answer(client, st, "A reasonable explanation").json()
    assert st["status"] == "completed" and st["end_reason"] == "end_max" and len(st["items"]) == 6


def test_reviewed_and_offline_resume_questions_are_not_asked_twice(client, container, fake):
    rid = ready_resume(container)
    offline = client.get(f"/api/resumes/{rid}/intelligence").json()["suggested_questions"][0]
    dup = {k: offline[k] for k in ("text", "rubric", "topic", "difficulty", "resume_id", "resume_name", "claim")}
    r = client.post("/api/interviews", json={"set_id": None, "config": {"include_bank": False, "max_followups": 0},
                                             "resume_questions": [dup], "resume_auto": {"resume_id": rid, "count": 4}})
    texts = [i["text"] for i in r.json()["items"]]
    assert texts.count(dup["text"]) == 1 and len(texts) == len(set(texts))      # asked once; the offline generator skipped it


def test_history_reports_the_planned_total_for_a_running_adaptive_interview(client, set_id, fake):
    """The dashboard's "Continue: question k of n" must not say "1 of 1" for an adaptive interview that plans more."""
    bank(client, set_id)
    st = start(client, set_id, max_questions=4)
    row = next(r for r in client.get("/api/interviews").json() if r["id"] == st["id"])
    assert row["total"] == 4 == st["progress"]["total"] and row["planned"] is True
    fake.chat_replies = [graded(7) for _ in range(4)]
    for _ in range(4):
        st = answer(client, st, "An answer").json()
    row = next(r for r in client.get("/api/interviews").json() if r["id"] == st["id"])
    assert st["status"] == "completed" and row["total"] == 4 and row["planned"] is False
