"""Base subject agent — shared logic for all four subject agents.

Each subject agent just provides a subject name and optional extra prompt;
the base handles mode selection, prompt rendering, and LLM call.
"""
from __future__ import annotations

import sqlite3

from src.nlp.llm import generate
from src.nlp.prompts import render


_MODE_TO_SYSTEM = {
    "default": "system_default",
    "socratic": "system_socratic",
    "eli5": "system_eli5",
}


def answer_question(
    conn: sqlite3.Connection,
    user_id: int,
    message: str,
    subject: str | None,
    topic: str | None,
    mode: str = "default",
) -> str:
    """Answer a student's doubt using the appropriate subject prompt + mode."""

    # 1. Build the system prompt from mode
    system_name = _MODE_TO_SYSTEM.get(mode, "system_default")
    system_prompt = render(system_name, question=message, topic=topic or "general")

    # 2. Build subject-specific context
    subject_prompt = ""
    if subject:
        subject_lower = subject.lower()
        try:
            subject_prompt = render(f"subject_{subject_lower}", question=message, topic=topic or "general")
        except FileNotFoundError:
            pass  # no subject-specific prompt, use system only

    # 3. Combine
    full_system = system_prompt
    if subject_prompt:
        full_system = f"{system_prompt}\n\n---\n\n{subject_prompt}"

    # 4. Call LLM
    result = generate(
        message,
        system=full_system,
        temperature=0.3,
        max_output_tokens=800,
    )

    return result.text


# Thin per-subject wrappers (for direct use by Agent map)

def _make_subject_answerer(subject: str):
    def answer(conn, user_id, message, topic=None, mode="default"):
        return answer_question(conn, user_id, message, subject, topic, mode)
    return answer
