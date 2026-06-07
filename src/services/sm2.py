"""SM-2 spaced repetition algorithm.

Reference: Wozniak, P. A. (1990). Optimization of repetition spacing in the
practice of learning. Acta Neurobiologiae Experimentalis 50.

Inputs:
- grade: int 0-5
        0 = total blackout
        1 = wrong, but recognized correct answer
        2 = wrong, easy to remember after seeing answer
        3 = correct, difficult
        4 = correct, with hesitation
        5 = perfect recall

State (per card):
- ease:    float, starts at 2.5, min 1.3
- interval: int (days), starts at 0
- reps:    int, starts at 0
- next_review: ISO date string (YYYY-MM-DD)

Behavior:
- grade < 3: reset reps=0, interval=1, leave ease alone
- grade >= 3:
    - reps == 0: interval = 1
    - reps == 1: interval = 6
    - reps >= 2: interval = round(prev_interval * ease)
    - ease = max(1.3, ease + 0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02))
    - reps += 1
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class CardState:
    ease: float = 2.5
    interval: int = 0
    reps: int = 0


def review(state: CardState, grade: int, today: date | None = None) -> tuple[CardState, date]:
    """Apply one SM-2 review. Returns (new_state, next_review_date)."""
    if not 0 <= grade <= 5:
        raise ValueError(f"grade must be 0..5, got {grade}")
    today = today or date.today()
    s = CardState(ease=state.ease, interval=state.interval, reps=state.reps)

    if grade < 3:
        s.reps = 0
        s.interval = 1
    else:
        if s.reps == 0:
            s.interval = 1
        elif s.reps == 1:
            s.interval = 6
        else:
            s.interval = max(1, round(s.interval * s.ease))
        # ease update
        s.ease = max(1.3, s.ease + 0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02))
        s.reps += 1

    return s, today + timedelta(days=s.interval)


def next_review_iso(new_state: CardState) -> str:
    """Compute the next_review ISO date for a state after a single review."""
    _, d = review(new_state, grade=4)  # placeholder; not used for storage
    return d.isoformat()
