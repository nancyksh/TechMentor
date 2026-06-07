"""End-to-end DB tests: schema applies, DAOs round-trip, FKs work."""
from __future__ import annotations

from src.db.dao import (
    UserDAO, SettingsDAO, SessionDAO, MessageDAO,
    QuizDAO, InterviewDAO, RoadmapDAO, ProblemDAO, CodeRunDAO, FlashcardDAO,
)


def test_user_get_or_create_default_idempotent(conn):
    a = UserDAO.get_or_create_default(conn, username="default")
    b = UserDAO.get_or_create_default(conn, username="default")
    assert a == b
    assert UserDAO.get(conn, a)["username"] == "default"


def test_settings_default_mode_set_and_get(conn, user_id):
    assert SettingsDAO.get_mode(conn, user_id) == "default"
    SettingsDAO.set_mode(conn, user_id, "socratic")
    assert SettingsDAO.get_mode(conn, user_id) == "socratic"
    SettingsDAO.set_mode(conn, user_id, "eli5")
    assert SettingsDAO.get_mode(conn, user_id) == "eli5"


def test_settings_rejects_invalid_mode(conn, user_id):
    import pytest
    with pytest.raises(ValueError):
        SettingsDAO.set_mode(conn, user_id, "bogus")


def test_session_and_message_round_trip(conn, user_id):
    sid = SessionDAO.create(conn, user_id, "chat", subject="OS", topic="deadlocks")
    MessageDAO.add(conn, sid, "user", "what is a deadlock?", subject="OS")
    MessageDAO.add(conn, sid, "assistant", "A deadlock is...", intent="DOUBT", subject="OS", mode="default")
    msgs = MessageDAO.list_for_session(conn, sid)
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["subject"] == "OS"
    by_subj = MessageDAO.recent_by_subject(conn, user_id)
    assert by_subj.get("OS") == 2


def test_quiz_attempt_round_trip_and_accuracy(conn, user_id):
    QuizDAO.create(conn, user_id, "DBMS", "normalization", "medium", 5, 4, 5, {"foo": "bar"})
    attempts = QuizDAO.list_for_user(conn, user_id, subject="DBMS")
    assert len(attempts) == 1
    assert attempts[0]["score"] == 4
    acc = QuizDAO.accuracy_by_topic(conn, user_id)
    assert abs(acc["normalization"] - 0.8) < 1e-9


def test_interview_session_with_questions_and_avg(conn, user_id):
    iid = InterviewDAO.start(conn, user_id, "technical")
    InterviewDAO.add_question(conn, iid, 1, "What is a thread?", "A unit of execution...",
                              0.8, 0.9, 0.7, "good")
    InterviewDAO.add_question(conn, iid, 2, "Explain deadlock.",
                              score_correctness=0.6, score_completeness=0.7, score_clarity=0.5,
                              feedback="needs depth")
    InterviewDAO.end(conn, iid, avg_score=0.7)
    qs = InterviewDAO.list_questions(conn, iid)
    assert len(qs) == 2
    assert qs[0]["seq"] == 1


def test_roadmap_replace_plan_and_list(conn, user_id):
    items = [
        {"week": 1, "subject": "OS", "topic": "deadlocks", "priority": 1, "rationale": "weak",
         "resources": [{"title": "Silberschatz Ch.7", "url": "", "kind": "book"}]},
        {"week": 1, "subject": "DBMS", "topic": "normalization", "priority": 2, "rationale": "ok",
         "resources": []},
    ]
    RoadmapDAO.replace_plan(conn, user_id, items)
    plan = RoadmapDAO.latest_for_user(conn, user_id)
    assert len(plan) == 2
    assert plan[0]["week"] == 1
    assert plan[0]["priority"] == 1


def test_problem_upsert_and_get_parses_json(conn):
    pid = ProblemDAO.upsert(
        conn, slug="t-sum", title="Two Sum", subject="DSA", topic="arrays",
        difficulty="easy", prompt="x", starter_code="x",
        test_cases=[{"stdin": "1 1", "expected": "0"}],
    )
    p = ProblemDAO.get(conn, pid)
    assert p is not None
    assert p["test_cases"] == [{"stdin": "1 1", "expected": "0"}]
    # upsert again — same slug, id stable
    pid2 = ProblemDAO.upsert(
        conn, slug="t-sum", title="Two Sum v2", subject="DSA", topic="arrays",
        difficulty="easy", prompt="x", starter_code="x",
        test_cases=[{"stdin": "1 1", "expected": "0"}],
    )
    assert pid == pid2
    assert ProblemDAO.get(conn, pid)["title"] == "Two Sum v2"


def test_code_run_and_best_for_problem(conn, user_id):
    pid = ProblemDAO.upsert(
        conn, slug="x", title="X", subject="DSA", topic="x",
        difficulty="easy", prompt="x", starter_code="x",
        test_cases=[{"stdin": "1", "expected": "1"}],
    )
    CodeRunDAO.create(conn, user_id, pid, "code1", passed=1, total=3, runtime_ms=50)
    CodeRunDAO.create(conn, user_id, pid, "code2", passed=3, total=3, runtime_ms=80)
    CodeRunDAO.create(conn, user_id, pid, "code3", passed=2, total=3, runtime_ms=20, error="x")
    best = CodeRunDAO.best_for_problem(conn, user_id, pid)
    assert best["passed"] == 3
    assert best["runtime_ms"] == 80


def test_flashcard_create_due_and_review_recall_rate(conn, user_id):
    cid = FlashcardDAO.create(conn, user_id, "OS", "deadlocks", "Q?", "A")
    card = FlashcardDAO.get(conn, cid)
    assert card["ease"] == 2.5
    assert card["reps"] == 0
    due = FlashcardDAO.due_today(conn, user_id)
    assert any(c["id"] == cid for c in due)
    # simulate two reviews
    FlashcardDAO.update_after_review(conn, cid, 2.6, 1, 1, "2099-01-01")
    FlashcardDAO.record_review(conn, cid, grade=4, prev_ease=2.5, prev_interval=0,
                                new_ease=2.6, new_interval=1)
    FlashcardDAO.update_after_review(conn, cid, 2.7, 3, 2, "2099-01-02")
    FlashcardDAO.record_review(conn, cid, grade=2, prev_ease=2.6, prev_interval=1,
                                new_ease=2.7, new_interval=3)
    rate = FlashcardDAO.recall_rate_by_topic(conn, user_id)
    # grades 4 and 2 -> one is >=3, one isn't -> 1/2 = 0.5
    assert abs(rate["deadlocks"] - 0.5) < 1e-9


def test_foreign_key_cascade_deletes_session_messages(conn, user_id):
    sid = SessionDAO.create(conn, user_id, "chat")
    MessageDAO.add(conn, sid, "user", "hi")
    # delete user -> sessions + messages cascade
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    n = conn.execute("SELECT COUNT(*) AS n FROM messages WHERE session_id = ?", (sid,)).fetchone()["n"]
    assert n == 0
