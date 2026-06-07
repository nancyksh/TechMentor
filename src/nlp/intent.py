"""Rule-based intent classifier.

Classifies a user message into:
- intent:   DOUBT | QUIZ | INTERVIEW | ROADMAP | CODE | FLASHCARD | CHITCHAT
- subject:  OS | DBMS | CN | DSA | None
- mode:     default | socratic | eli5  (teaching style toggle)
- topic:    free-form keyword(s) inferred from the message

Design:
- Pure Python, no LLM call, <1ms per call.
- Keyword sets are explicit and easy to extend.
- Returns a dataclass so the supervisor can route on typed fields.

If a message has no clear intent, we fall back to DOUBT (most common case).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

VALID_INTENTS = {"DOUBT", "QUIZ", "INTERVIEW", "ROADMAP", "CODE", "FLASHCARD", "CHITCHAT"}
VALID_SUBJECTS = {"OS", "DBMS", "CN", "DSA"}
VALID_MODES = {"default", "socratic", "eli5"}


@dataclass
class Classification:
    intent: str
    subject: str | None = None
    mode: str = "default"
    topic: str | None = None
    confidence: float = 1.0
    signals: list[str] = field(default_factory=list)


# ---------- keyword tables ----------

_INTENT_KEYWORDS: list[tuple[str, list[str]]] = [
    ("QUIZ", [
        r"\bquiz\b", r"\bmcqs?\b", r"\bmultiple choice\b", r"\btest me\b",
        r"\bquestion(s)?\b.*\bfor me\b", r"\bgenerate.*questions?\b",
    ]),
    ("INTERVIEW", [
        r"\binterview\b", r"\bmock\b", r"\bhr\b.*\bquestion", r"\btech(nical)?\b.*\bround\b",
    ]),
    ("ROADMAP", [
        r"\broadmap\b", r"\bstudy plan\b", r"\blearning path\b",
        r"\bwhere should i start\b", r"\bwhat should i (study|learn|revise)\b",
    ]),
    ("CODE", [
        r"\b(run|execute|test)\b.*\bcode\b", r"\bcode lab\b", r"\bsubmit\b.*\bsolution\b",
        r"\bmy (solution|code|program)\b",
    ]),
    ("FLASHCARD", [
        r"\bflash(card)?s?\b", r"\breview\b", r"\bspaced repetition\b",
        r"\bdue (today|now)\b", r"\bmemor(y|ize)\b",
    ]),
]

_SUBJECT_KEYWORDS: list[tuple[str, list[str]]] = [
    ("OS", [
        r"\boperat(ing)?\s*system(s)?\b", r"\bos\b", r"\bscheduling\b", r"\bdeadlock(s)?\b",
        r"\bsynchron(ization|ize)\b", r"\bmemory management\b", r"\bvirtual memory\b",
        r"\bprocess(es)?\b", r"\bthread(s|ing)?\b", r"\bsemaphore(s)?\b", r"\bmutex\b",
    ]),
    ("DBMS", [
        r"\bdbms\b", r"\bdatabase(s)?\b", r"\bsql\b", r"\bnormalization\b", r"\bnf\b",
        r"\bindexing\b", r"\btransaction(s)?\b", r"\bacid\b", r"\bschema\b",
        r"\bjoin(s)?\b", r"\bforeign key", r"\bprimary key", r"\ber diagram\b",
    ]),
    ("CN", [
        r"\bcomputer network(s|ing)?\b", r"\bcn\b", r"\btcp\b", r"\bip\b", r"\bosi\b",
        r"\brouting\b", r"\bsubnet(ting)?\b", r"\bprotocol(s)?\b", r"\bcongestion\b",
        r"\bhttp(s)?\b", r"\bdns\b", r"\bmac address\b",
    ]),
    ("DSA", [
        r"\bdsa\b", r"\bdata structure(s)?\b", r"\balgorithm(s)?\b", r"\barray(s)?\b",
        r"\blinked list\b", r"\btree(s)?\b", r"\bgraph(s)?\b", r"\bsort(ing)?\b",
        r"\bdynamic programming\b", r"\bdp\b", r"\brecursion\b", r"\bstack\b", r"\bqueue\b",
        r"\bhash( table| map)?\b", r"\bbinary search\b", r"\bbst\b", r"\bheap\b",
    ]),
]

_MODE_KEYWORDS: list[tuple[str, list[str]]] = [
    ("socratic", [
        r"\bsocratic\b", r"\bask me\b", r"\bguide me\b", r"\bdon'?t (just )?tell\b",
        r"\bwith (guiding )?questions\b", r"\bteach me to think\b",
    ]),
    ("eli5", [
        r"\beli5\b", r"\bexplain (like|as if) i'?m (5|five|new|newbie|a (kid|child))\b",
        r"\bsimpl(e|ify|ify it)\b", r"\banalog(y|ies)\b", r"\breal[- ]world example\b",
    ]),
]


def _match_any(patterns: list[str], text: str) -> list[str]:
    hits = []
    for p in patterns:
        if re.search(p, text, flags=re.IGNORECASE):
            hits.append(p)
    return hits


def classify(message: str, *, default_subject: str | None = None,
             default_mode: str = "default") -> Classification:
    """Classify a free-form user message.

    Order of checks (first match wins for intent):
        1. mode keywords (socratic / eli5) override default_mode
        2. intent keywords
        3. subject keywords
        4. fallback: intent=DOUBT, subject=default_subject or None
    """
    text = (message or "").strip()
    if not text:
        return Classification(intent="CHITCHAT", subject=default_subject, mode=default_mode)

    # ---- mode (override) ----
    mode = default_mode
    signals: list[str] = []
    for m, patterns in _MODE_KEYWORDS:
        if _match_any(patterns, text):
            mode = m
            signals.append(f"mode:{m}")
            break

    # ---- intent ----
    intent = "DOUBT"  # default
    for i, patterns in _INTENT_KEYWORDS:
        if _match_any(patterns, text):
            intent = i
            signals.append(f"intent:{i}")
            break

    # ---- subject ----
    subject = default_subject
    for s, patterns in _SUBJECT_KEYWORDS:
        if _match_any(patterns, text):
            subject = s
            signals.append(f"subject:{s}")
            break

    # ---- topic (best-effort: take the longest capitalized / known noun phrase) ----
    topic = _extract_topic(text)

    confidence = min(1.0, 0.4 + 0.15 * len(signals))

    return Classification(
        intent=intent,
        subject=subject,
        mode=mode if mode in VALID_MODES else "default",
        topic=topic,
        confidence=confidence,
        signals=signals,
    )


def _extract_topic(text: str) -> str | None:
    """Cheap topic extraction: look for known CS terms in the message.

    Not exhaustive; the subject agent will refine it via the LLM.
    """
    KNOWN = [
        "deadlock", "starvation", "scheduling", "paging", "thrashing",
        "normalization", "1nf", "2nf", "3nf", "bcnf", "indexing", "transactions",
        "acid", "joins", "subquery", "view", "trigger", "stored procedure",
        "osi model", "tcp/ip", "subnetting", "routing", "congestion control",
        "binary search", "linked list", "binary tree", "b tree", "b+ tree", "heap",
        "graph", "bfs", "dfs", "dijkstra", "dynamic programming", "greedy",
        "recursion", "backtracking", "hash map", "hash table", "trie", "segment tree",
        "sorting", "quicksort", "mergesort", "insertion sort", "bubble sort",
        "avl", "red black tree",
    ]
    lower = text.lower()
    for term in KNOWN:
        if term in lower:
            return term
    # fall back to last noun-ish word
    words = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", text)
    return words[-1] if words else None
