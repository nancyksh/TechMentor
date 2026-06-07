"""Weakness heatmap builder.

Aggregates mastery data from the DB and returns a grid suitable for Plotly.

Output format:
{
    "subjects": ["OS", "DBMS", "CN", "DSA"],
    "topics":  ["deadlocks", "normalization", "routing", ...],
    "grid":    [[0.0, 0.5, ...], ...]   # subjects × topics, 0-100 mastery %
}
"""
from __future__ import annotations

import sqlite3
from typing import Any

# Canonical topics per subject (used to fill missing data as 0% mastery).
SUBJECT_TOPICS: dict[str, list[str]] = {
    "OS":   ["processes", "threads", "scheduling", "deadlocks", "synchronization",
             "memory management", "virtual memory", "file systems", "io"],
    "DBMS": ["er modeling", "relational model", "sql", "normalization", "indexing",
             "transactions", "acid", "concurrency control", "query optimization"],
    "CN":   ["osi model", "tcp/ip", "physical layer", "data link layer", "network layer",
             "transport layer", "application layer", "routing", "congestion control"],
    "DSA":  ["arrays", "linked lists", "stacks", "queues", "trees", "graphs",
             "hashing", "sorting", "searching", "dynamic programming", "greedy"],
}


def build_heatmap(conn: sqlite3.Connection, user_id: int) -> dict[str, Any]:
    """Build a weakness heatmap for the given user.

    Mastery sources (weighted):
    - Quiz accuracy by topic   (weight 0.40)
    - Flashcard recall by topic (weight 0.30)
    - Interview avg score by subject (weight 0.15, broadcast to topics)
    - Message doubt count by subject (negative signal: more doubts → lower mastery, weight 0.15)
    """
    subjects = list(SUBJECT_TOPICS.keys())
    # Build a flat topic list per subject for grid alignment
    topic_map: dict[str, list[str]] = {s: list(ts) for s, ts in SUBJECT_TOPICS.items()}
    all_topics = [t for ts in topic_map.values() for t in ts]

    # Initialise grid with 0
    grid: list[list[float]] = [[0.0] * len(all_topics) for _ in subjects]
    topic_idx = {t: i for i, t in enumerate(all_topics)}

    # --- Quiz accuracy ---
    rows = conn.execute(
        """SELECT COALESCE(topic, subject) AS k,
                  CAST(SUM(score) AS REAL) / NULLIF(SUM(total), 0) AS acc
           FROM quiz_attempts WHERE user_id = ? GROUP BY k""",
        (user_id,),
    ).fetchall()
    for r in rows:
        k = (r["k"] or "").lower()
        acc = (r["acc"] or 0.0) * 100
        if k in topic_idx:
            si = _subject_index(k, subjects)
            if si is not None:
                grid[si][topic_idx[k]] += acc * 0.40

    # --- Flashcard recall ---
    rows = conn.execute(
        """SELECT f.topic,
                  CAST(SUM(CASE WHEN r.grade >= 3 THEN 1 ELSE 0 END) AS REAL) / COUNT(*) AS rate
           FROM flashcard_reviews r
           JOIN flashcards f ON f.id = r.card_id
           WHERE f.user_id = ? GROUP BY f.topic""",
        (user_id,),
    ).fetchall()
    for r in rows:
        k = (r["topic"] or "").lower()
        rate = (r["rate"] or 0.0) * 100
        if k in topic_idx:
            si = _subject_index(k, subjects)
            if si is not None:
                grid[si][topic_idx[k]] += rate * 0.30

    # --- Interview avg by subject ---
    rows = conn.execute(
        """SELECT s.subject, AVG(i.avg_score) AS avg_s
           FROM interview_sessions i
           JOIN sessions s ON s.id = i.session_id
           WHERE s.user_id = ? AND s.subject IS NOT NULL
           GROUP BY s.subject""",
        (user_id,),
    ).fetchall()
    for r in rows:
        subj = (r["subject"] or "").upper()
        avg = (r["avg_s"] or 0.0) * 100
        if subj in topic_map:
            si = subjects.index(subj)
            for t in topic_map[subj]:
                grid[si][topic_idx[t]] += avg * 0.15

    # --- Doubt count (negative signal: more doubts → cap mastery) ---
    rows = conn.execute(
        """SELECT m.subject, COUNT(*) AS n
           FROM messages m
           JOIN sessions s ON s.id = m.session_id
           WHERE s.user_id = ? AND m.subject IS NOT NULL
           GROUP BY m.subject""",
        (user_id,),
    ).fetchall()
    max_doubts = max((r["n"] for r in rows), default=1) or 1
    for r in rows:
        subj = (r["subject"] or "").upper()
        n = r["n"]
        if subj in topic_map:
            si = subjects.index(subj)
            # More doubts → subtract up to 15% from each topic
            penalty = (n / max_doubts) * 15
            for t in topic_map[subj]:
                grid[si][topic_idx[t]] = max(0, grid[si][topic_idx[t]] - penalty)

    # Clamp to 0-100
    for row in grid:
        for i in range(len(row)):
            row[i] = max(0.0, min(100.0, row[i]))

    return {
        "subjects": subjects,
        "topics": all_topics,
        "grid": grid,
    }


def _subject_index(topic_or_subject: str, subjects: list[str]) -> int | None:
    t = topic_or_subject.upper()
    for i, s in enumerate(subjects):
        if s.upper() == t:
            return i
    # heuristic: if topic is in a subject's topic list, find that subject
    for s, ts in SUBJECT_TOPICS.items():
        if topic_or_subject.lower() in [x.lower() for x in ts]:
            return subjects.index(s)
    return None
