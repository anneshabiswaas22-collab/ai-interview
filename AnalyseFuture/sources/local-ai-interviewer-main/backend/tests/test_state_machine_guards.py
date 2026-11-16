"""Guard branches of the interview state machine: invalid input, actions during an evaluation, and stale model results.

These paths are what keep an interview consistent when the browser, the user or the model does something unexpected."""
from app.schemas import MAX_ANSWER_CHARS
from conftest import act, add_questions, answer, good_eval, start_interview, state


def _evaluating(container, iid):
    with container.db.tx() as c:
        c.execute("UPDATE interviews SET phase='evaluating' WHERE id=?", (iid,))


def test_over_long_and_empty_answers_are_rejected_and_change_nothing(client, set_id, fake):
    add_questions(client, set_id, 1)
    st = start_interview(client, set_id)
    r = answer(client, st, "x" * (MAX_ANSWER_CHARS + 1))
    assert r.status_code == 400 and r.json()["error"]["code"] == "answer_too_long"
    r = answer(client, st, "   ")
    assert r.status_code == 400 and r.json()["error"]["code"] == "empty_answer"
    assert state(client, st["id"])["phase"] == "awaiting_answer" and not fake.chat_calls


def test_end_delete_and_clear_wait_for_a_running_evaluation(client, container, set_id):
    add_questions(client, set_id, 1)
    st = start_interview(client, set_id)
    _evaluating(container, st["id"])
    for r in (client.post(f"/api/interviews/{st['id']}/end"), client.delete(f"/api/interviews/{st['id']}"),
              client.delete("/api/interviews?confirm=true")):
        assert r.status_code == 409 and r.json()["error"]["code"] == "evaluating"
    assert client.delete("/api/interviews").status_code == 400                      # clearing history needs confirm=true


def test_resume_of_a_running_interview_and_skip_with_nothing_to_skip(client, container, set_id):
    add_questions(client, set_id, 1)
    st = start_interview(client, set_id)
    r = client.post(f"/api/interviews/{st['id']}/resume")
    assert r.status_code == 409 and r.json()["error"]["code"] == "not_paused"
    with container.db.tx() as c:                                                    # the current turn was already evaluated
        c.execute("UPDATE turns SET status='evaluated' WHERE id=?", (st["current_turn_id"],))
    r = act(client, st, "skip")
    assert r.status_code == 409 and r.json()["error"]["code"] == "not_skippable"


def test_a_stale_evaluation_result_is_dropped(client, container, set_id, fake):
    """The model finishes after the interview moved on (ended / deleted): its result must not change anything."""
    add_questions(client, set_id, 2)
    st = start_interview(client, set_id, max_followups=0)
    svc = container.interviews
    turn_id = st["current_turn_id"]
    with container.db.tx() as c:
        c.execute("UPDATE turns SET status='submitted', answer_text='kept' WHERE id=?", (turn_id,))
    svc._evaluate(st["id"], turn_id)                                                # not 'evaluating': obsolete, no model call
    assert not fake.chat_calls
    from app.schemas import LLMEvaluation
    _evaluating(container, st["id"])
    with container.db.tx() as c:
        c.execute("UPDATE interviews SET current_turn_id=-1 WHERE id=?", (st["id"],))   # superseded meanwhile
    svc._apply(st["id"], turn_id, LLMEvaluation.model_validate(good_eval()))
    with container.db.read() as c:
        row = c.execute("SELECT status, evaluation_json FROM turns WHERE id=?", (turn_id,)).fetchone()
    assert row["status"] == "submitted" and row["evaluation_json"] is None


def test_skipping_a_followup_in_after_followups_mode_shows_feedback(client, set_id, fake):
    add_questions(client, set_id, 2)
    fake.chat_replies = [good_eval(correctness=5, followup="Why would a MERGE fail under late data?", missing=["Idempotency"])]
    st = start_interview(client, set_id, max_followups=1, feedback_mode="after_followups")
    st = answer(client, st).json()
    assert st["phase"] == "awaiting_answer" and st["current"]["turn"]["kind"] == "followup"
    st = act(client, st, "skip").json()
    assert st["phase"] == "feedback" and st["current"]["item"]["position"] == 0
