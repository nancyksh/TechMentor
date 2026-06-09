"""LLM wrapper around google-genai.

Public API:
    from src.nlp.llm import generate, generate_json, count_tokens

    text = generate(prompt, system="...", temperature=0.4)
    obj  = generate_json(prompt, system="...", schema_hint={...})

Design:
- Lazy client (built on first use; reads GEMINI_API_KEY from env).
- Latency + token accounting returned alongside content.
- Retries with exponential backoff on transient errors.
- Errors raise LLMError with a clear message.
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any

_client = None
_model_name: str | None = None


class LLMError(RuntimeError):
    pass


def _get_client():
    global _client, _model_name
    if _client is None:
        try:
            from google import genai
        except ImportError as e:
            raise LLMError(
                "google-genai not installed. Run: pip install -r requirements.txt"
            ) from e
        key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not key or key == "your_gemini_api_key_here":
            raise LLMError("GEMINI_API_KEY missing. Set it in .env.")
        _client = genai.Client(api_key=key)
        _model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip()
    return _client, _model_name


@dataclass
class LLMResult:
    text: str
    latency_ms: int
    prompt_tokens: int
    output_tokens: int
    total_tokens: int
    model: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "latency_ms": self.latency_ms,
            "prompt_tokens": self.prompt_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "model": self.model,
        }


def _extract_json(text: str) -> dict | list:
    """Best-effort JSON extraction from a model response.

    Strategy: try strict json.loads first, then strip ```json ... ``` fences,
    then find the first balanced { ... } or [ ... ] block.
    """
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```(?:json)?\s*(\{.*\}|\[.*\])\s*```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass

    for opener, closer in [("{", "}"), ("[", "]")]:
        i = text.find(opener)
        if i == -1:
            continue
        depth, j = 0, i
        in_str, esc = False, False
        while j < len(text):
            c = text[j]
            if in_str:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    in_str = False
            else:
                if c == '"':
                    in_str = True
                elif c == opener:
                    depth += 1
                elif c == closer:
                    depth -= 1
                    if depth == 0:
                        candidate = text[i : j + 1]
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            break
            j += 1
    raise LLMError(f"Could not parse JSON from model output: {text[:200]!r}")


def _call_with_retry(call_fn, *, max_retries: int = 3):
    last_err: Exception | None = None
    for attempt in range(max_retries):
        try:
            return call_fn()
        except Exception as e:  # broad: SDK raises various types
            last_err = e
            msg = str(e).lower()
            transient = any(
                k in msg
                for k in ("429", "500", "502", "503", "504", "timeout", "unavailable", "rate")
            )
            if not transient or attempt == max_retries - 1:
                break
            time.sleep(1.5 ** attempt)
    raise LLMError(f"LLM call failed after {max_retries} attempts: {last_err}")


def generate(
    prompt: str,
    *,
    system: str | None = None,
    temperature: float = 0.4,
    max_output_tokens: int = 1024,
    model: str | None = None,
) -> LLMResult:
    """Single-turn text generation."""
    client, default_model = _get_client()
    chosen = model or default_model
    contents = prompt
    config: dict[str, Any] = {
        "temperature": temperature,
        "max_output_tokens": max_output_tokens,
    }
    if system:
        config["system_instruction"] = system

    def _do():
        t0 = time.perf_counter()
        resp = client.models.generate_content(model=chosen, contents=contents, config=config)
        dt_ms = int((time.perf_counter() - t0) * 1000)
        text = (resp.text or "").strip()
        um = getattr(resp, "usage_metadata", None) or {}
        return LLMResult(
            text=text,
            latency_ms=dt_ms,
            prompt_tokens=int(getattr(um, "prompt_token_count", 0) or 0),
            output_tokens=int(getattr(um, "candidates_token_count", 0) or 0),
            total_tokens=int(getattr(um, "total_token_count", 0) or 0),
            model=chosen,
        )

    return _call_with_retry(_do)


def generate_json(
    prompt: str,
    *,
    system: str | None = None,
    schema_hint: str | None = None,
    temperature: float = 0.2,
    max_output_tokens: int = 2048,
    model: str | None = None,
) -> tuple[dict | list, LLMResult]:
    """Single-turn generation that returns parsed JSON + the raw LLMResult.

    schema_hint: a short string appended to the prompt telling the model the desired shape.
    """
    extra = ""
    if schema_hint:
        extra = f"\n\nReturn ONLY valid JSON matching this shape:\n{schema_hint}\nDo not wrap in markdown fences."
    raw = generate(
        prompt + extra,
        system=system,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        model=model,
    )
    obj = _extract_json(raw.text)
    return obj, raw


def count_tokens(text: str, *, model: str | None = None) -> int:
    """Approximate token count (chars/4). For accurate counts, model.count_tokens is preferred."""
    return max(1, len(text) // 4)
