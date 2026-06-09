"""Quiz Generation Agent — produces MCQ quizzes via Gemini."""
from __future__ import annotations

import sqlite3
from typing import Any

from src.nlp.llm import generate_json
from src.nlp.prompts import render
from src.db.dao import QuizDAO, SessionDAO


def generate_quiz(
    conn: sqlite3.Connection,
    user_id: int,
    subject: str | None,
    topic: str | None,
    difficulty: str = "medium",
    num_questions: int = 5,
) -> dict[str, Any]:
    """Generate a quiz and persist it. Returns the quiz dict."""
    prompt = render(
        "quiz_gen",
        num_questions=num_questions,
        subject=subject or "CS general",
        topic=topic or "mixed topics",
        difficulty=difficulty,
    )
    obj, llm_result = generate_json(
        prompt,
        system="You are TechMentor, a precise CS quiz generator. Output only valid JSON.",
        temperature=0.7,
        max_output_tokens=4096,
    )

    # Persist
    questions = obj.get("questions", [])
    if questions:
        sid = SessionDAO.create(conn, user_id, "quiz", subject=subject, topic=topic)
        QuizDAO.create(
            conn, user_id, subject=subject or "general", topic=topic,
            difficulty=difficulty, num_questions=len(questions),
            score=0, total=len(questions), details=obj, session_id=sid,
        )
        return {"questions": questions, "session_id": sid, "subject": subject, "topic": topic}

    return {"questions": [], "session_id": None, "subject": subject, "topic": topic}
