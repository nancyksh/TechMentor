# 04 — Architecture Decision Records (ADRs)

> Short, dated records of significant design decisions.
> Format: context → decision → consequences.

---

## ADR-001 — LLM choice: Google Gemini over OpenAI / local
**Date:** 2026-06-04
**Context:** Need a free, capable, low-latency LLM for a 1-week single-semester project.
**Decision:** Use Google Gemini (`gemini-1.5-flash` default, `gemini-1.5-pro` fallback) via `google-generativeai` SDK.
**Consequences:**
- No cost; generous free tier (15 RPM, 1M TPM on flash)
- Slightly different prompting style than OpenAI; we standardize on a few-shot system prompt template
- Switch to another LLM = change `GEMINI_MODEL` env + one wrapper function

## ADR-002 — Skip RAG knowledge base for v1
**Date:** 2026-06-04
**Context:** Building a 1-week MVP; RAG would add KB curation + chunking + embedding ingestion overhead.
**Decision:** Rely on Gemini's built-in knowledge + carefully crafted domain prompts. Retrieval module kept in `src/nlp/retrieval.py` for future use.
**Consequences:**
- Faster to ship
- Slight risk of hallucination on edge CS topics; mitigated by evaluation set in `data/eval/`
- Retrieval code is dormant but ready to enable

## ADR-003 — CrewAI as orchestrator
**Date:** 2026-06-04
**Context:** Synopsis mandates CrewAI; alternatives are LangChain agents and bare function calls.
**Decision:** Use CrewAI. The Supervisor is a `Crew` with a router tool; subject/quiz/interview/roadmap are `Agent`s.
**Consequences:**
- Aligns with synopsis
- Slight learning curve; documented in `AGENT.md`
- Easy to extend with more agents

## ADR-004 — Deploy on Hugging Face Spaces (Docker SDK)
**Date:** 2026-06-04
**Context:** Need a free, public, always-on URL for the demo. Streamlit Community Cloud and HF Spaces are the two main options.
**Decision:** HF Spaces with Docker SDK for reproducibility.
**Consequences:**
- Public URL like `https://nancyksh-techmentor.hf.space`
- Docker required (handled by HF; no local Docker install)
- `Dockerfile` ships with the repo for local parity

## ADR-005 — SQLite for persistence
**Date:** 2026-06-04
**Context:** Single-user/single-session scope. Need persistent quiz attempts and roadmap state.
**Decision:** SQLite via stdlib `sqlite3`. Schema in `src/db/schema.sql`; migrations as numbered files in `src/db/migrations/`.
**Consequences:**
- Zero-setup, file-based
- Trivially upgradeable to Postgres later by swapping the DAO

## ADR-006 — Skip local Docker during build week
**Date:** 2026-06-04
**Context:** User explicitly said "worry about Docker some other time". HF Spaces provides the Docker runtime at deploy.
**Decision:** Author `Dockerfile` + `docker-compose.yml` for completeness and HF deploy, but skip local Docker install.
**Consequences:**
- Faster build, less for user to install
- Image is only validated on HF Spaces (no local pre-flight)

## ADR-007 — Skip voice (STT/TTS) for v1
**Date:** 2026-06-04
**Context:** 1-week deadline; voice adds latency, dependencies, audio handling.
**Decision:** Text-only v1. Voice marked as future enhancement.
**Consequences:**
- Smaller dep tree
- Speech module stub kept in `src/utils/` for future
