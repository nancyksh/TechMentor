"""Supervisor tests — classification + routing + persistence."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.nlp.intent import classify
from src.nlp.llm import LLMResult
from src.db.dao import MessageDAO, SettingsDAO


def _mock_generate(*args, **kwargs):
    return LLMResult(
        text="A semaphore is a synchronization primitive used to control access to shared resources.",
        latency_ms=100, prompt_tokens=50, output_tokens=30, total_tokens=80,
        model="gemini-2.5-flash",
    )


def _mock_generate_question(*args, **kwargs):
    return LLMResult(
        text="What is the difference between a mutex and a semaphore?",
        latency_ms=100, prompt_tokens=50, output_tokens=30, total_tokens=80,
        model="gemini-2.5-flash",
    )


def _mock_generate_json_quiz(*args, **kwargs):
    return (
        {"questions": [
            {"id": "q1", "question": "What is 3NF?",
             "choices": ["A) ...", "B) ...", "C) ...", "D) ..."],
             "answer_index": 0, "explanation": "3NF ensures no transitive dependencies."},
        ]},
        LLMResult(text='{"questions":[]}', latency_ms=100,
                  prompt_tokens=50, output_tokens=30, total_tokens=80,
                  model="gemini-2.5-flash"),
    )


def _mock_generate_json_interview(*args, **kwargs):
    return (
        {"question": "What is a deadlock?", "expected_points": ["mutual exclusion"], "difficulty": "medium"},
        LLMResult(text='{"question":""}', latency_ms=100,
                  prompt_tokens=50, output_tokens=30, total_tokens=80,
                  model="gemini-2.5-flash"),
    )


def _mock_generate_json_roadmap(*args, **kwargs):
    return (
        {"summary": "You need to focus on OS.", "weeks": [{"week": 1, "items": [
            {"subject": "OS", "topic": "deadlocks", "priority": 1, "rationale": "weak",
             "resources": [], "estimated_hours": 4}
        ]}]},
        LLMResult(text='{"summary":""}', latency_ms=100,
                  prompt_tokens=50, output_tokens=30, total_tokens=80,
                  model="gemini-2.5-flash"),
    )


def _mock_generate_json_chitchat(*args, **kwargs):
    return LLMResult(
        text="Hello! I'm TechMentor. Ask me about OS, DBMS, CN, or DSA!",
        latency_ms=100, prompt_tokens=50, output_tokens=30, total_tokens=80,
        model="gemini-2.5-flash",
    )


# ---------- classify tests (no LLM needed) ----------

def test_classify_returns_valid_intent_and_subject():
    cls = classify("What is a deadlock in OS?")
    assert cls.intent in {"DOUBT", "QUIZ", "INTERVIEW", "ROADMAP", "CODE", "FLASHCARD", "CHITCHAT"}
    assert cls.subject in {None, "OS", "DBMS", "CN", "DSA"}
    assert cls.mode in {"default", "socratic", "eli5"}


# ---------- Supervisor tests (with mocks) ----------

@patch("src.nlp.llm.generate", side_effect=_mock_generate)
def test_supervisor_persists_messages(mock_gen, conn, user_id):
    from src.supervisor import Supervisor
    sup = Supervisor(user_id, conn)
    response = sup.process("What is a semaphore?")
    assert sup.session_id is not None
    msgs = MessageDAO.list_for_session(conn, sup.session_id)
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[0]["content"] == "What is a semaphore?"
    assert msgs[1]["role"] == "assistant"
    assert msgs[1]["subject"] == "OS"


@patch("src.agents.subjects.base.generate", side_effect=_mock_generate_question)
def test_supervisor_mode_override(mock_gen, conn, user_id):
    from src.supervisor import Supervisor
    sup = Supervisor(user_id, conn)
    response = sup.process("Tell me about deadlocks", mode_override="socratic")
    assert "?" in response.content
    assert response.mode == "socratic"


@patch("src.agents.quiz.generate_json", side_effect=_mock_generate_json_quiz)
def test_supervisor_classifies_quiz_intent(mock_gen, conn, user_id):
    from src.supervisor import Supervisor
    sup = Supervisor(user_id, conn)
    response = sup.process("Give me a quiz on DBMS normalization")
    assert response.intent == "QUIZ"
    assert response.subject == "DBMS"


@patch("src.nlp.llm.generate", side_effect=_mock_generate)
def test_supervisor_creates_session(mock_gen, conn, user_id):
    from src.supervisor import Supervisor
    sup = Supervisor(user_id, conn)
    assert sup.session_id is None
    sup.process("Hello")
    assert sup.session_id is not None


@patch("src.nlp.llm.generate", side_effect=_mock_generate)
def test_supervisor_reuses_session(mock_gen, conn, user_id):
    from src.supervisor import Supervisor
    sup = Supervisor(user_id, conn)
    sup.process("What is TCP?")
    sid = sup.session_id
    sup.process("What is UDP?")
    assert sup.session_id == sid
    msgs = MessageDAO.list_for_session(conn, sid)
    assert len(msgs) == 4


def test_settings_mode_persists(conn, user_id):
    SettingsDAO.set_mode(conn, user_id, "eli5")
    assert SettingsDAO.get_mode(conn, user_id) == "eli5"
    from src.supervisor import Supervisor
    sup = Supervisor(user_id, conn)
    assert sup._mode == "eli5"
