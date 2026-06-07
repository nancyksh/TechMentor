"""NLP foundation: LLM wrapper, intent classifier, prompt loader, retrieval stubs."""
from .llm import generate, generate_json, count_tokens, LLMResult, LLMError
from .intent import classify, Classification, VALID_INTENTS, VALID_SUBJECTS, VALID_MODES
from .prompts import render, render_strict, load, list_prompts
from .retrieval import EmbeddingStore, encode, Hit

__all__ = [
    "generate", "generate_json", "count_tokens", "LLMResult", "LLMError",
    "classify", "Classification", "VALID_INTENTS", "VALID_SUBJECTS", "VALID_MODES",
    "render", "render_strict", "load", "list_prompts",
    "EmbeddingStore", "encode", "Hit",
]
