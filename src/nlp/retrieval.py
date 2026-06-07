"""Retrieval-augmented generation helpers (DORMANT for v1, ready to enable).

Per ADR-002 we rely on the LLM's built-in knowledge in v1 and keep this
module for future use without a behavior change. Set ENABLE_RETRIEVAL=true
in .env and the subject agents will use it.

Components:
- EmbeddingStore: in-memory list of (id, text, vector) backed by numpy.
- encode(texts): Sentence-BERT encode with a lazy-loaded model.
- top_k(query, k=3): cosine-similarity retrieval.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np

_MODEL = None


def _get_model():
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer
        name = os.environ.get("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        cache = os.environ.get("EMBEDDING_CACHE_DIR") or None
        _MODEL = SentenceTransformer(name, cache_folder=cache)
    return _MODEL


def encode(texts: list[str]) -> np.ndarray:
    """Encode a list of texts into L2-normalized vectors (cosine-friendly)."""
    m = _get_model()
    v = m.encode(texts, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)
    return v.astype(np.float32)


@dataclass
class Hit:
    id: str
    text: str
    score: float


class EmbeddingStore:
    """Minimal in-memory store. Add documents, query with cosine similarity."""

    def __init__(self) -> None:
        self._ids: list[str] = []
        self._texts: list[str] = []
        self._vecs: np.ndarray | None = None  # shape (N, D), normalized

    def __len__(self) -> int:
        return len(self._ids)

    def add(self, ids: list[str], texts: list[str]) -> None:
        if not ids:
            return
        assert len(ids) == len(texts), "ids and texts must be same length"
        vecs = encode(texts)
        if self._vecs is None:
            self._vecs = vecs
        else:
            self._vecs = np.vstack([self._vecs, vecs])
        self._ids.extend(ids)
        self._texts.extend(texts)

    def query(self, text: str, k: int = 3) -> list[Hit]:
        if self._vecs is None or len(self._ids) == 0:
            return []
        q = encode([text])[0]
        scores = self._vecs @ q  # cosine sim (vectors are normalized)
        order = np.argsort(-scores)[:k]
        return [
            Hit(id=self._ids[i], text=self._texts[i], score=float(scores[i]))
            for i in order
        ]

    def clear(self) -> None:
        self._ids.clear()
        self._texts.clear()
        self._vecs = None
