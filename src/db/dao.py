"""Data Access Objects. Thin wrappers over sqlite3 — keep SQL in one place.

Design:
- DAOs accept a sqlite3.Connection (caller controls transactions).
- Return sqlite3.Row (dict-like) or plain dicts / lists.
- No ORM, no magic. Easy to read, easy to test.

For v1 all DAOs live in one file. Split per-table files when this exceeds ~500 lines.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime
from typing import Any, Iterable


# ============================================================
# Helpers
# ============================================================

def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def _rows_to_dicts(rows: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(r) for r in rows]


def _today_iso() -> str:
    return date.today().isoformat()


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


# ============================================================
# Users
# ============================================================

class UserDAO:
    TABLE = "users"

    @staticmethod
    def get_or_create_default(conn: sqlite3.Connection, username: str = "default") -> int:
        row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if row:
            return row["id"]
        cur = conn.execute(
            "INSERT INTO users (username, display_name) VALUES (?, ?)",
            (username, username.title()),
        )
        # also seed default settings row
        conn.execute(
            "INSERT OR IGNORE INTO settings (user_id, default_mode) VALUES (?, 'default')",
            (cur.lastrowid,),
        )
        return cur.lastrowid

    @staticmethod
    def get(conn: sqlite3.Connection, user_id: int) -> dict | None:
        return _row_to_dict(
            conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        )


# ============================================================
# Settings
# ============================================================

class SettingsDAO:
    @staticmethod
    def get_mode(conn: sqlite3.Connection, user_id: int) -> str:
        row = conn.execute(
            "SELECT default_mode FROM settings WHERE user_id = ?", (user_id,)
        ).fetchone()
        return row["default_mode"] if row else "default"

    @staticmethod
    def set_mode(conn: sqlite3.Connection, user_id: int, mode: str) -> None:
        if mode not in ("default", "socratic", "eli5"):
            raise ValueError(f"invalid mode: {mode}")
        conn.execute(
            "UPDATE settings SET default_mode = ?, updated_at = datetime('now') WHERE user_id = ?",
            (mode, user_id),
        )


# ============================================================
# Sessions + Messages (chat history)
# ============================================================

class SessionDAO:
    @staticmethod
    def create(
        conn: sqlite3.Connection,
        user_id: int,
        kind: str,
        subject: str | None = None,
        topic: str | None = None,
    ) -> int:
        cur = conn.execute(
            "INSERT INTO sessions (user_id, kind, subject, topic) VALUES (?,?,?,?)",
            (user_id, kind, subject, topic),
        )
        return cur.lastrowid

    @staticmethod
    def end(conn: sqlite3.Connection, session_id: int) -> None:
        conn.execute(
            "UPDATE sessions SET ended_at = datetime('now') WHERE id = ?",
            (session_id,),
        )

    @staticmethod
    def list_for_user(
        conn: sqlite3.Connection, user_id: int, kind: str | None = None, limit: int = 50
    ) -> list[dict]:
        if kind:
            rows = conn.execute(
                "SELECT * FROM sessions WHERE user_id = ? AND kind = ? ORDER BY started_at DESC LIMIT ?",
                (user_id, kind, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM sessions WHERE user_id = ? ORDER BY started_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        return _rows_to_dicts(rows)


class MessageDAO:
    @staticmethod
    def add(
        conn: sqlite3.Connection,
        session_id: int,
        role: str,
        content: str,
        intent: str | None = None,
        subject: str | None = None,
        mode: str | None = None,
        tokens: int | None = None,
        latency_ms: int | None = None,
    ) -> int:
        cur = conn.execute(
            """INSERT INTO messages
               (session_id, role, content, intent, subject, mode, tokens, latency_ms)
               VALUES (?,?,?,?,?,?,?,?)""",
            (session_id, role, content, intent, subject, mode, tokens, latency_ms),
        )
        return cur.lastrowid

    @staticmethod
    def list_for_session(conn: sqlite3.Connection, session_id: int) -> list[dict]:
        rows = conn.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        ).fetchall()
        return _rows_to_dicts(rows)

    @staticmethod
    def recent_by_subject(
        conn: sqlite3.Connection, user_id: int, limit: int = 100
    ) -> dict[str, int]:
        """Return {subject: msg_count} for messages from this user (last `limit` messages)."""
        rows = conn.execute(
            """SELECT m.subject, COUNT(*) AS n
               FROM messages m
               JOIN sessions s ON s.id = m.session_id
               WHERE s.user_id = ? AND m.subject IS NOT NULL
               GROUP BY m.subject""",
            (user_id,),
        ).fetchall()
        return {r["subject"]: r["n"] for r in rows}


# ============================================================
# Quiz attempts
# ============================================================

class QuizDAO:
    @staticmethod
    def create(
        conn: sqlite3.Connection,
        user_id: int,
        subject: str,
        topic: str | None,
        difficulty: str,
        num_questions: int,
        score: int,
        total: int,
        details: dict,
        session_id: int | None = None,
    ) -> int:
        cur = conn.execute(
            """INSERT INTO quiz_attempts
               (user_id, session_id, subject, topic, difficulty, num_questions, score, total, details)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                user_id, session_id, subject, topic, difficulty,
                num_questions, score, total, json.dumps(details),
            ),
        )
        return cur.lastrowid

    @staticmethod
    def list_for_user(
        conn: sqlite3.Connection, user_id: int, subject: str | None = None, limit: int = 50
    ) -> list[dict]:
        if subject:
            rows = conn.execute(
                "SELECT * FROM quiz_attempts WHERE user_id = ? AND subject = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, subject, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM quiz_attempts WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        return _rows_to_dicts(rows)

    @staticmethod
    def accuracy_by_topic(
        conn: sqlite3.Connection, user_id: int
    ) -> dict[str, float]:
        rows = conn.execute(
            """SELECT COALESCE(topic, subject) AS k,
                      CAST(SUM(score) AS REAL) / NULLIF(SUM(total), 0) AS acc
               FROM quiz_attempts
               WHERE user_id = ?
               GROUP BY k""",
            (user_id,),
        ).fetchall()
        return {r["k"]: (r["acc"] or 0.0) for r in rows}


# ============================================================
# Interview sessions + questions
# ============================================================

class InterviewDAO:
    @staticmethod
    def start(
        conn: sqlite3.Connection, user_id: int, track: str, session_id: int | None = None
    ) -> int:
        cur = conn.execute(
            "INSERT INTO interview_sessions (user_id, session_id, track) VALUES (?,?,?)",
            (user_id, session_id, track),
        )
        return cur.lastrowid

    @staticmethod
    def add_question(
        conn: sqlite3.Connection,
        interview_id: int,
        seq: int,
        question: str,
        answer: str | None = None,
        score_correctness: float | None = None,
        score_completeness: float | None = None,
        score_clarity: float | None = None,
        feedback: str | None = None,
    ) -> int:
        cur = conn.execute(
            """INSERT INTO interview_questions
               (interview_id, seq, question, answer, score_correctness,
                score_completeness, score_clarity, feedback)
               VALUES (?,?,?,?,?,?,?,?)""",
            (interview_id, seq, question, answer, score_correctness,
             score_completeness, score_clarity, feedback),
        )
        return cur.lastrowid

    @staticmethod
    def end(
        conn: sqlite3.Connection, interview_id: int, avg_score: float
    ) -> None:
        conn.execute(
            "UPDATE interview_sessions SET ended_at = datetime('now'), avg_score = ? WHERE id = ?",
            (avg_score, interview_id),
        )

    @staticmethod
    def list_questions(conn: sqlite3.Connection, interview_id: int) -> list[dict]:
        rows = conn.execute(
            "SELECT * FROM interview_questions WHERE interview_id = ? ORDER BY seq ASC",
            (interview_id,),
        ).fetchall()
        return _rows_to_dicts(rows)


# ============================================================
# Roadmap
# ============================================================

class RoadmapDAO:
    @staticmethod
    def replace_plan(
        conn: sqlite3.Connection, user_id: int, items: list[dict]
    ) -> None:
        """Wipe and re-insert the user's roadmap (simple, v1)."""
        conn.execute("DELETE FROM roadmap_items WHERE user_id = ?", (user_id,))
        conn.executemany(
            """INSERT INTO roadmap_items
               (user_id, week, subject, topic, priority, rationale, resources)
               VALUES (?,?,?,?,?,?,?)""",
            [
                (
                    user_id, it["week"], it["subject"], it["topic"],
                    it["priority"], it.get("rationale"),
                    json.dumps(it.get("resources", [])),
                )
                for it in items
            ],
        )

    @staticmethod
    def latest_for_user(conn: sqlite3.Connection, user_id: int) -> list[dict]:
        rows = conn.execute(
            "SELECT * FROM roadmap_items WHERE user_id = ? ORDER BY week, priority",
            (user_id,),
        ).fetchall()
        return _rows_to_dicts(rows)

    @staticmethod
    def mark_completed(conn: sqlite3.Connection, item_id: int, completed: bool = True) -> None:
        conn.execute(
            "UPDATE roadmap_items SET completed = ? WHERE id = ?",
            (1 if completed else 0, item_id),
        )


# ============================================================
# Problems (DSA) + Code runs
# ============================================================

class ProblemDAO:
    @staticmethod
    def upsert(
        conn: sqlite3.Connection,
        slug: str,
        title: str,
        subject: str,
        topic: str,
        difficulty: str,
        prompt: str,
        starter_code: str,
        test_cases: list[dict],
        reference: str | None = None,
        time_limit_ms: int = 3000,
    ) -> int:
        conn.execute(
            """INSERT INTO problems
               (slug, title, subject, topic, difficulty, prompt, starter_code, test_cases, reference, time_limit_ms)
               VALUES (?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(slug) DO UPDATE SET
                 title=excluded.title, subject=excluded.subject, topic=excluded.topic,
                 difficulty=excluded.difficulty, prompt=excluded.prompt,
                 starter_code=excluded.starter_code, test_cases=excluded.test_cases,
                 reference=excluded.reference, time_limit_ms=excluded.time_limit_ms""",
            (
                slug, title, subject, topic, difficulty, prompt,
                starter_code, json.dumps(test_cases), reference, time_limit_ms,
            ),
        )
        return conn.execute(
            "SELECT id FROM problems WHERE slug = ?", (slug,)
        ).fetchone()["id"]

    @staticmethod
    def get(conn: sqlite3.Connection, problem_id: int) -> dict | None:
        row = conn.execute("SELECT * FROM problems WHERE id = ?", (problem_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["test_cases"] = json.loads(d["test_cases"])
        return d

    @staticmethod
    def list_all(
        conn: sqlite3.Connection, topic: str | None = None, difficulty: str | None = None
    ) -> list[dict]:
        q = "SELECT id, slug, title, subject, topic, difficulty FROM problems"
        clauses, args = [], []
        if topic:
            clauses.append("topic = ?")
            args.append(topic)
        if difficulty:
            clauses.append("difficulty = ?")
            args.append(difficulty)
        if clauses:
            q += " WHERE " + " AND ".join(clauses)
        q += " ORDER BY topic, difficulty, title"
        rows = conn.execute(q, args).fetchall()
        return _rows_to_dicts(rows)


class CodeRunDAO:
    @staticmethod
    def create(
        conn: sqlite3.Connection,
        user_id: int,
        problem_id: int,
        code: str,
        passed: int,
        total: int,
        runtime_ms: int | None = None,
        error: str | None = None,
        session_id: int | None = None,
    ) -> int:
        cur = conn.execute(
            """INSERT INTO code_runs
               (user_id, problem_id, session_id, code, passed, total, runtime_ms, error)
               VALUES (?,?,?,?,?,?,?,?)""",
            (user_id, problem_id, session_id, code, passed, total, runtime_ms, error),
        )
        return cur.lastrowid

    @staticmethod
    def best_for_problem(
        conn: sqlite3.Connection, user_id: int, problem_id: int
    ) -> dict | None:
        row = conn.execute(
            """SELECT * FROM code_runs
               WHERE user_id = ? AND problem_id = ?
               ORDER BY (CAST(passed AS REAL) / total) DESC, runtime_ms ASC
               LIMIT 1""",
            (user_id, problem_id),
        ).fetchone()
        return _row_to_dict(row)


# ============================================================
# Flashcards (SM-2)
# ============================================================

class FlashcardDAO:
    @staticmethod
    def create(
        conn: sqlite3.Connection,
        user_id: int,
        subject: str,
        topic: str,
        front: str,
        back: str,
    ) -> int:
        cur = conn.execute(
            """INSERT INTO flashcards
               (user_id, subject, topic, front, back, next_review)
               VALUES (?,?,?,?,?, date('now'))""",
            (user_id, subject, topic, front, back),
        )
        return cur.lastrowid

    @staticmethod
    def get(conn: sqlite3.Connection, card_id: int) -> dict | None:
        return _row_to_dict(
            conn.execute("SELECT * FROM flashcards WHERE id = ?", (card_id,)).fetchone()
        )

    @staticmethod
    def due_today(
        conn: sqlite3.Connection, user_id: int, limit: int = 20
    ) -> list[dict]:
        rows = conn.execute(
            """SELECT * FROM flashcards
               WHERE user_id = ? AND next_review <= date('now')
               ORDER BY next_review ASC, id ASC
               LIMIT ?""",
            (user_id, limit),
        ).fetchall()
        return _rows_to_dicts(rows)

    @staticmethod
    def all_for_user(
        conn: sqlite3.Connection, user_id: int, limit: int = 200
    ) -> list[dict]:
        rows = conn.execute(
            "SELECT * FROM flashcards WHERE user_id = ? ORDER BY next_review ASC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return _rows_to_dicts(rows)

    @staticmethod
    def update_after_review(
        conn: sqlite3.Connection,
        card_id: int,
        new_ease: float,
        new_interval: int,
        new_reps: int,
        next_review_iso: str,
    ) -> None:
        conn.execute(
            """UPDATE flashcards
               SET ease = ?, interval = ?, reps = ?, next_review = ?
               WHERE id = ?""",
            (new_ease, new_interval, new_reps, next_review_iso, card_id),
        )

    @staticmethod
    def record_review(
        conn: sqlite3.Connection,
        card_id: int,
        grade: int,
        prev_ease: float,
        prev_interval: int,
        new_ease: float,
        new_interval: int,
    ) -> int:
        cur = conn.execute(
            """INSERT INTO flashcard_reviews
               (card_id, grade, prev_ease, prev_interval, new_ease, new_interval)
               VALUES (?,?,?,?,?,?)""",
            (card_id, grade, prev_ease, prev_interval, new_ease, new_interval),
        )
        return cur.lastrowid

    @staticmethod
    def recall_rate_by_topic(
        conn: sqlite3.Connection, user_id: int
    ) -> dict[str, float]:
        """For each topic, ratio of grades >= 3 over total reviews."""
        rows = conn.execute(
            """SELECT f.topic,
                      CAST(SUM(CASE WHEN r.grade >= 3 THEN 1 ELSE 0 END) AS REAL) / COUNT(*) AS rate
               FROM flashcard_reviews r
               JOIN flashcards f ON f.id = r.card_id
               WHERE f.user_id = ?
               GROUP BY f.topic""",
            (user_id,),
        ).fetchall()
        return {r["topic"]: (r["rate"] or 0.0) for r in rows}
