"""Pytest fixtures: ephemeral DB per test session."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure repo root on path
_repo = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, _repo)

# Load .env so GEMINI_API_KEY is available for tests that call the LLM
from dotenv import load_dotenv
load_dotenv(Path(_repo) / ".env")

# Point at a temp DB BEFORE importing connection
_tmp = Path(tempfile.gettempdir()) / "techmentor_test.db"
if _tmp.exists():
    _tmp.unlink()
os.environ["APP_DB_PATH"] = str(_tmp)

from src.db.connection import init_schema  # noqa: E402
from src.db.dao import UserDAO  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _apply_schema():
    init_schema()
    yield


@pytest.fixture()
def conn():
    """Fresh connection per test, wrapped in a transaction that rolls back on teardown."""
    from src.db.connection import connect
    c = connect()
    yield c
    c.close()


@pytest.fixture()
def user_id(conn):
    return UserDAO.get_or_create_default(conn)
