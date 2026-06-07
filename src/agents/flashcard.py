"""Flashcard Agent — generates cards and manages SM-2 spaced repetition."""
from __future__ import annotations

import sqlite3
from typing import Any

from src.nlp.llm import generate_json
from src.nlp.prompts import render
from src.db.dao import FlashcardDAO
from src.services.sm2 import review, CardState


def generate_cards(
    conn: sqlite3.Connection,
    user_id: int,
    subject: str | None,
    topic: str | None,
    num_cards: int = 5,
) -> list[dict[str, Any]]:
    """Generate flashcards from a subject/topic and persist them."""
    prompt = render(
        "flashcard_gen",
        num_cards=num_cards,
        subject=subject or "CS general",
        topic=topic or "mixed topics",
    )
    obj, _ = generate_json(
        prompt,
        system="You are TechMentor, a concise flashcard maker. Output only valid JSON.",
        temperature=0.5,
    )
    cards = obj.get("cards", [])
    persisted = []
    for c in cards:
        cid = FlashcardDAO.create(conn, user_id, subject or "general", topic or "general", c["front"], c["back"])
        persisted.append({"id": cid, "front": c["front"], "back": c["back"]})
    return persisted


def get_due_cards(conn: sqlite3.Connection, user_id: int, limit: int = 20) -> list[dict]:
    """Get flashcards due today for the user."""
    return FlashcardDAO.due_today(conn, user_id, limit)


def grade_card(conn: sqlite3.Connection, card_id: int, grade: int) -> dict:
    """Grade a flashcard and update SM-2 state. Returns new card state."""
    card = FlashcardDAO.get(conn, card_id)
    if not card:
        raise ValueError(f"Card {card_id} not found")

    state = CardState(ease=card["ease"], interval=card["interval"], reps=card["reps"])
    new_state, next_review = review(state, grade)

    # Record the review
    FlashcardDAO.record_review(
        conn, card_id, grade,
        prev_ease=state.ease, prev_interval=state.interval,
        new_ease=new_state.ease, new_interval=new_state.interval,
    )
    FlashcardDAO.update_after_review(
        conn, card_id, new_state.ease, new_state.interval, new_state.reps,
        next_review.isoformat(),
    )

    return {
        "card_id": card_id,
        "grade": grade,
        "new_ease": new_state.ease,
        "new_interval": new_state.interval,
        "new_reps": new_state.reps,
        "next_review": next_review.isoformat(),
    }
