"""Smoke test for the Gemini API key using the new google-genai SDK.
Run from project root: .venv/Scripts/python scripts/smoke_gemini.py
"""
import os
import sys
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

key = os.environ.get("GEMINI_API_KEY", "").strip()
preferred = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash").strip()

if not key or key == "your_gemini_api_key_here":
    print("FAIL: GEMINI_API_KEY missing or unset in .env")
    sys.exit(1)

print(f"Key length: {len(key)} chars, prefix: {key[:6]}...")

try:
    from google import genai
    client = genai.Client(api_key=key)

    # Step 1: list available models (proves auth works, reveals what's allowed)
    print("\n--- Available models (first 12) ---")
    models = list(client.models.list(config={"page_size": 30}))
    shown = 0
    for m in models:
        name = getattr(m, "name", "")
        methods = getattr(m, "supported_generation_methods", [])
        if "generateContent" in methods or "generate_content" in str(methods).lower() or True:
            print(f"  {name}  methods={methods}")
            shown += 1
            if shown >= 12:
                break

    # Step 2: try preferred model
    print(f"\n--- Trying preferred model: {preferred} ---")
    try:
        resp = client.models.generate_content(model=preferred, contents="Reply with exactly: PONG")
        print(f"OK: -> {resp.text.strip()[:80]}")
    except Exception as e1:
        print(f"Preferred failed: {type(e1).__name__}: {str(e1)[:200]}")
        # try first available
        for m in models:
            name = getattr(m, "name", "")
            if "/" in name and "gemini" in name.lower():
                test_name = name.split("/")[-1] if "/" in name else name
                try:
                    print(f"  fallback -> {test_name}")
                    resp = client.models.generate_content(model=test_name, contents="Reply with exactly: PONG")
                    print(f"OK with {test_name}: -> {resp.text.strip()[:80]}")
                    print(f"\nUpdate .env: GEMINI_MODEL={test_name}")
                    sys.exit(0)
                except Exception as e2:
                    print(f"  failed: {str(e2)[:120]}")
        print("No working model found. Check API key permissions.")
        sys.exit(3)

except Exception as e:
    print(f"FATAL: {type(e).__name__}: {e}")
    sys.exit(2)
