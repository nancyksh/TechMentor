"""SQLite connection helper.

Usage:
    from src.db.connection import connect, transaction
    with connect() as conn:
        conn.execute(...)
    # or
    with transaction() as conn:
        conn.execute(...)

Path is read from APP_DB_PATH env var (default ./data/techmentor.db).
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

_SCHEMA_FILE = Path(__file__).resolve().parent / "schema.sql"


def _resolve_db_path() -> Path:
    raw = os.environ.get("APP_DB_PATH", "./data/techmentor.db")
    p = Path(raw).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def connect(row_factory: bool = True) -> sqlite3.Connection:
    """Open a connection. Defaults to dict-style rows for ergonomics."""
    conn = sqlite3.connect(
        _resolve_db_path(),
        detect_types=sqlite3.PARSE_DECLTYPES,
        check_same_thread=False,
        timeout=10.0,
    )
    if row_factory:
        conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def transaction() -> Iterator[sqlite3.Connection]:
    """Context manager: commits on success, rolls back on error."""
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_schema() -> None:
    """Apply schema.sql to the configured DB. Idempotent (uses IF NOT EXISTS)."""
    sql = _SCHEMA_FILE.read_text(encoding="utf-8")
    with transaction() as conn:
        conn.executescript(sql)


if __name__ == "__main__":
    init_schema()
    print(f"OK: schema applied -> {_resolve_db_path()}")
