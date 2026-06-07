"""Apply the SQL schema. Idempotent.

Usage:
    python scripts/init_db.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.db.connection import init_schema  # noqa: E402

if __name__ == "__main__":
    init_schema()
    print("OK: schema applied.")
