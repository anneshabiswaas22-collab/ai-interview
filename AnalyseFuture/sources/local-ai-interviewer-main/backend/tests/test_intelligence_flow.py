"""Interview Intelligence 2.0 end to end: profile-aware grading, grounding, provenance, consistency, analytics and privacy."""
import json
import sqlite3

from conftest import answer, start_interview
from intel_fixtures import graded


def add(client, set_id, text, topic=None, difficulty=None):
    r = client.post(f"/api/sets/{set_id}/questions", json={"text": text, "topic": topic, "difficulty": difficulty})
    assert r.status_code == 201


def test_sql_question_is_graded_with_the_sql_profile_and_full_provenance(client, set_id, fake):
    add(client, set_id, "Explain LEFT JOIN semantics.", "SQL", "medium")
    fake.chat_replies = [graded(8, evidence=[{"kind": "correct", "point": "keeps left rows", "quote": "keeps all rows from the left"}])]
    st = start_interview(client, set_id, max_followups=0)
    st = answer(client, st, "It keeps all rows from the left table and NULLs the rest").json()
    req = fake.chat_calls[0]
    schema = req["format"]
    assert "edge_cases" in schema["properties"]["dimension_scores"]["required"]            # the profile's extra dimensions were requested
    assert "EVALUATION PROFILE: SQL" in req["messages"][0]["content"]
    ev = st["current"]["thread"][0]["evaluation"]
    assert ev["profile"] == "sql" and ev["classification"] == "correct" and ev["evidence"][0]["verified"] is True
    assert abs(sum(ev["weights"].values()) - 1) < 0.01
    prov = ev["provenance"]
    assert prov["prompt_version"] == "eval-2.0" and prov["rubric"].startswith("sql-v") and prov["input_hash"] and prov["graded_by"]["model"]
    assert "temperature" in prov


def test_model_supplied_total_is_ignored(client, set_id, fake):
    add(client, set_id, "What is a primary key?", "SQL", "easy")
    fake.chat_replies = [graded(4, extra={"score": 10, "verdict": "Excellent", "classification": "correct"})]
    st = start_interview(client, set_id, max_followups=0)
    ev = answer(client, st, "It identifies rows").json()["current"]["thread"][0]["evaluation"]
    assert ev["score"] == 4.0 and ev["verdict"] == "Weak"


def test_identical_input_gives_identical_hash_and_score(client, set_id, fake):
    add(client, set_id, "What is a primary key?", "SQL", "easy")
    scores, hashes = [], []
    for i in range(2):
        st = start_interview(client, set_id, max_followups=0, replace=bool(i))     # replacing ends the first one (its summary uses a model call)
        fake.chat_replies = [graded(7)]
        ev = answer(client, st, "It uniquely identifies each row").json()["current"]["thread"][0]["evaluation"]
        scores.append(ev["score"])
        hashes.append(ev["provenance"]["input_hash"])
    assert scores[0] == scores[1] and hashes[0] == hashes[1]


def test_repair_retry_then_success(client, set_id, fake):
    add(client, set_id, "What is a primary key?")
    fake.chat_replies = ["{broken", graded(7)]
    st = start_interview(client, set_id, max_followups=0)
    st = answer(client, st, "It identifies rows").json()
    assert st["phase"] == "feedback" and len(fake.chat_calls) == 2


def test_i_dont_know_is_capped_and_gets_no_followup(client, set_id, fake):
    add(client, set_id, "Explain the CAP theorem.")
    fake.chat_replies = [graded(6, correct=[], followup="Which two properties hold under partition?")]
    st = start_interview(client, set_id, max_followups=2)
    st = answer(client, st, "I don't know").json()
    ev = st["current"]["thread"][0]["evaluation"]
    assert ev["classification"] == "no_attempt" and ev["score"] <= 2 and ev["adjustments"] and st["next_action"] != "followup"


def test_unverified_misconception_is_not_counted_as_an_error(client, set_id, fake):
    add(client, set_id, "Explain indexes.", "SQL")
    fake.chat_replies = [graded(5, misconceptions=["Thinks indexes slow down reads"])]
    st = start_interview(client, set_id, max_followups=0)
    ev = answer(client, st, "Indexes speed up lookups on columns").json()["current"]["thread"][0]["evaluation"]
    assert ev["misconceptions"] == [] and ev["unverified_misconceptions"] == ["Thinks indexes slow down reads"]
    assert ev["classification"] != "incorrect"


def test_behavioural_interview_uses_the_behavioural_profile(client, set_id, fake):
    add(client, set_id, "Tell me about a time you handled conflict.")
    fake.chat_replies = [graded(7)]
    st = start_interview(client, set_id, max_followups=0, interview_type="hr")
    assert answer(client, st, "Situation, task, action, result").json()["current"]["thread"][0]["evaluation"]["profile"] == "behavioral"
    req = fake.chat_calls[0]
    assert "Behavioural" in req["messages"][0]["content"] and "edge_cases" not in req["format"]["properties"]["dimension_scores"]["properties"]


def test_report_intelligence_progress_and_learning_plan(client, set_id, fake):
    add(client, set_id, "What is a primary key?", "SQL", "easy")
    add(client, set_id, "How do generators work?", "Python", "hard")
    for i, (a, b) in enumerate([(4, 5), (8, 6)]):
        fake.chat_replies = [graded(a), graded(b)]
        st = start_interview(client, set_id, max_followups=0, replace=bool(i), feedback_mode="at_end")
        st = answer(client, st, "answer one").json()
        st = answer(client, st, "answer two").json()
    rep = client.get(f"/api/interviews/{st['id']}/report").json()
    intel = rep["intelligence"]
    assert {d["difficulty"] for d in intel["difficulty"]} == {"easy", "hard"}
    assert intel["conceptual_vs_practical"]["conceptual"] is not None
    assert {p["key"] for p in intel["profiles"]} == {"sql", "python"}
    sql = next(p for p in rep["progress"] if p["topic"] == "SQL")
    assert sql["previous"] == 4.0 and sql["delta"] == 4.0
    assert intel["learning_plan"] and all(p["action"] for p in intel["learning_plan"])
    md = client.get(f"/api/interviews/{st['id']}/report/export?format=md").text
    assert "## Assessment detail" in md and "Learning plan" in md


def test_redacted_export_removes_answers_quotes_and_usage(client, set_id, fake):
    add(client, set_id, "What is a primary key?")
    fake.chat_replies = [graded(7, evidence=[{"kind": "correct", "point": "x", "quote": "my secret answer text"}])]
    st = start_interview(client, set_id, max_followups=0, feedback_mode="at_end")
    st = answer(client, st, "my secret answer text here").json()
    full = client.get(f"/api/interviews/{st['id']}/report/export?format=json").text
    red = client.get(f"/api/interviews/{st['id']}/report/export?format=json&redact=true").text
    assert "my secret answer text" in full and "my secret answer text" not in red and json.loads(red)["redacted"] is True
    assert "my secret answer text" not in client.get(f"/api/interviews/{st['id']}/report/export?format=md&redact=true").text
    assert client.get(f"/api/interviews/{st['id']}/report/export?format=pdf&redact=true").status_code == 200


def test_backup_is_a_consistent_sqlite_copy(client, set_id, tmp_path):
    add(client, set_id, "Backup me?")
    r = client.get("/api/backup")
    assert r.status_code == 200 and r.headers["cache-control"] == "no-store"
    out = tmp_path / "b.sqlite3"
    out.write_bytes(r.content)
    conn = sqlite3.connect(out)
    assert conn.execute("SELECT COUNT(*) FROM questions WHERE text='Backup me?'").fetchone()[0] == 1
    assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_backup_is_blocked_cross_site(client):
    assert client.get("/api/backup", headers={"host": "evil.example"}).status_code == 403


def test_profiles_endpoint(client):
    data = client.get("/api/evaluation/profiles").json()
    assert {"sql", "python", "data_engineering", "machine_learning", "system_design", "software_engineering", "behavioral", "general"} <= {p["key"] for p in data["profiles"]}


def test_old_evaluations_without_v6_fields_still_report(client, container, set_id, fake):
    add(client, set_id, "Legacy?")
    fake.chat_replies = [graded(7)]
    st = start_interview(client, set_id, max_followups=0, feedback_mode="at_end")
    st = answer(client, st, "x").json()
    with container.db.tx() as c:                    # strip the v6 fields as if the evaluation had been stored by v5
        row = c.execute("SELECT id, evaluation_json FROM turns").fetchone()
        ev = json.loads(row["evaluation_json"])
        for k in ("profile", "classification", "evidence", "weights", "provenance", "consistency_flags", "adjustments", "unverified_misconceptions"):
            ev.pop(k, None)
        c.execute("UPDATE turns SET evaluation_json=? WHERE id=?", (json.dumps(ev), row["id"]))
        c.execute("DELETE FROM reports")
        from app.services import reports
        reports.store_report(c, st["id"])
    rep = client.get(f"/api/interviews/{st['id']}/report").json()
    assert rep["summary"]["average_score"] == 7.0 and rep["intelligence"]["classifications"] == []


def test_redaction_is_an_allow_list_across_all_formats(client, container, fake):
    """Fable finding: model prose quotes the answer. A sentinel in the answer, the grader's text and the resume must vanish everywhere."""
    from intel_fixtures import ready_resume
    import pypdfium2 as pdfium
    S = "ZEBRASENTINEL"
    rid = ready_resume(container, name=f"{S}_CV")
    with container.db.tx() as c:
        c.execute("UPDATE resumes SET profile_json=replace(profile_json, 'Acme Corp', ?), raw_text=replace(raw_text, 'Acme Corp', ?)", (S, S))
    r = client.post("/api/interviews", json={"set_id": None, "config": {"include_bank": False, "max_followups": 1, "feedback_mode": "at_end"},
                                             "resume_auto": {"resume_id": rid, "count": 2}})
    st = r.json()
    leaky = graded(6, correct=[f"Mentioned {S} pipeline"], missing=[f"{S} detail"], misconceptions=[f"said {S}"],
                   followup=f"What about {S} retries?", extra={"verdict_summary": f"{S} answer", "uncertainty_note": S, "ideal_answer": S})
    fake.chat_replies = [leaky, graded(7), graded(7), {"overall_summary": S, "strengths": [S], "knowledge_gaps": [], "repeated_misconceptions": [],
                                                       "topics_to_revise": [], "recommendations": [S]}]
    for _ in range(3):
        if st["status"] != "in_progress":
            break
        st = answer(client, st, f"I built the {S} pipeline myself").json()
    iid = st["id"]
    full = client.get(f"/api/interviews/{iid}/report/export?format=json").text
    assert S in full
    for fmt in ("json", "md"):
        assert S not in client.get(f"/api/interviews/{iid}/report/export?format={fmt}&redact=true").text, fmt
    pdf = client.get(f"/api/interviews/{iid}/report/export?format=pdf&redact=true").content
    doc = pdfium.PdfDocument(pdf)
    text = "".join(doc[i].get_textpage().get_text_range() for i in range(len(doc)))
    assert "Interview Report" in text and S not in text


def test_backup_never_uses_the_shared_temp_folder_and_cleans_leftovers(client, container):
    folder = container.settings.data_dir / "tmp"
    folder.mkdir(parents=True, exist_ok=True)
    stale = folder / "interviewer-backup-old.sqlite3"
    stale.write_bytes(b"x")
    assert client.get("/api/backup").status_code == 200
    assert not stale.exists() and not list(folder.glob("interviewer-backup-*.sqlite3"))
