"""Interview Preparation Agent — generates questions and evaluates answers."""
from __future__ import annotations

from typing import Any

from src.nlp.llm import generate_json
from src.nlp.prompts import render


def generate_question(
    track: str = "technical",
    subject: str | None = None,
    seq: int = 1,
    prev_answer: str | None = None,
    prev_feedback: str | None = None,
) -> dict[str, Any]:
    """Generate the next interview question."""
    prev_ctx = ""
    if prev_answer:
        prev_ctx = (
            f"The candidate's previous answer was: \"{prev_answer}\"\n"
            f"Feedback given: \"{prev_feedback or 'N/A'}\"\n"
            "Make the next question slightly more probing based on that."
        )

    prompt = render(
        "interview_gen",
        track=track,
        subject=subject or "CS general",
        seq=seq,
        prev_context=prev_ctx,
    )
    obj, _ = generate_json(
        prompt,
        system="You are TechMentor, a structured interview coach. Output only valid JSON.",
        temperature=0.6,
    )
    return obj


def evaluate_answer(
    track: str,
    question: str,
    expected_points: list[str],
    answer: str,
) -> dict[str, Any]:
    """Evaluate a student's interview answer."""
    points_str = "\n".join(f"- {p}" for p in expected_points)
    prompt = render(
        "interview_eval",
        track=track,
        question=question,
        expected_points=points_str,
        answer=answer,
    )
    obj, _ = generate_json(
        prompt,
        system="You are TechMentor, a strict but fair interview evaluator. Output only valid JSON.",
        temperature=0.2,
        max_output_tokens=4096,
    )
    return obj
