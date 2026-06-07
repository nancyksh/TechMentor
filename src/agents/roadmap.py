"""Study Roadmap Agent — generates personalized study plans from session history."""
from __future__ import annotations

import json
import sqlite3
from typing import Any

from src.nlp.llm import generate_json
from src.nlp.prompts import render
from src.db.dao import RoadmapDAO, MessageDAO, QuizDAO, FlashcardDAO


def generate_roadmap(
    conn: sqlite3.Connection,
    user_id: int,
) -> dict[str, Any]:
    """Build an activity snapshot from the DB and generate a 4-week roadmap."""
    # 1. Gather activity snapshot
    snapshot = _build_snapshot(conn, user_id)
    snapshot_str = json.dumps(snapshot, indent=2)

    # 2. Generate roadmap via LLM
    prompt = render("roadmap_gen", activity_snapshot=snapshot_str)
    obj, _ = generate_json(
        prompt,
        system="You are TechMentor, a personalized study planner. Output only valid JSON.",
        temperature=0.4,
        max_output_tokens=2048,
    )

    # 3. Persist to DB
    weeks = obj.get("weeks", [])
    items = []
    for week in weeks:
        for item in week.get("items", []):
            items.append({
                "week": week["week"],
                "subject": item.get("subject", "general"),
                "topic": item.get("topic", ""),
                "priority": item.get("priority", 5),
                "rationale": item.get("rationale", ""),
                "resources": item.get("resources", []),
            })
    if items:
        RoadmapDAO.replace_plan(conn, user_id, items)

    obj["summary"] = obj.get("summary", "Based on your activity, here is your personalized 4-week study plan.")
    return obj


def _build_snapshot(conn: sqlite3.Connection, user_id: int) -> dict[str, Any]:
    """Build a JSON-serializable activity snapshot for the LLM."""
    # Quiz accuracy by subject/topic
    quiz_acc = QuizDAO.accuracy_by_topic(conn, user_id)

    # Flashcard recall by topic
    recall = FlashcardDAO.recall_rate_by_topic(conn, user_id)

    # Message counts by subject
    msg_counts = MessageDAO.recent_by_subject(conn, user_id)

    # Combine
    topics_data = {}
    all_topics = set(quiz_acc.keys()) | set(recall.keys()) | set(msg_counts.keys())
    for t in all_topics:
        topics_data[t] = {
            "quiz_accuracy": round(quiz_acc.get(t, 0), 2),
            "flashcard_recall": round(recall.get(t, 0), 2),
            "doubt_count": msg_counts.get(t, 0),
        }

    return {
        "user_id": user_id,
        "total_quiz_attempts": sum(1 for _ in QuizDAO.list_for_user(conn, user_id)),
        "topics": topics_data,
    }
