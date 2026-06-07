"""Prompt template loader.

Prompt files live in `data/prompts/*.md` and use Python str.format placeholders.

Usage:
    from src.nlp.prompts import render
    sys_prompt = render("subject_os", topic="deadlocks")
"""
from __future__ import annotations

from pathlib import Path
from string import Template
from typing import Any

_PROMPTS_DIR = Path(__file__).resolve().parents[2] / "data" / "prompts"


def _resolve(name: str) -> Path:
    p = _PROMPTS_DIR / f"{name}.md"
    if not p.exists():
        raise FileNotFoundError(f"Prompt template not found: {p}")
    return p


def load(name: str) -> str:
    """Load a prompt template verbatim (no interpolation)."""
    return _resolve(name).read_text(encoding="utf-8")


def render(name: str, **vars: Any) -> str:
    """Load a prompt and substitute ${var} placeholders (Template.safe_substitute).

    Missing vars are left as ${var} (no KeyError) so partial templates work.
    For strict substitution use render_strict.
    """
    text = load(name)
    return Template(text).safe_substitute(**vars)


def render_strict(name: str, **vars: Any) -> str:
    text = load(name)
    return Template(text).substitute(**vars)


def list_prompts() -> list[str]:
    return sorted(p.stem for p in _PROMPTS_DIR.glob("*.md"))
