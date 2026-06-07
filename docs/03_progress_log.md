# 03 — Progress Log

> Day-by-day build journal. One section per working day. Newest at the top.

---

## Day 1 — Project bootstrap ✅
**Date:** 2026-06-04
**Phases completed:** 0
**Phases in flight:** 1, 2
**Status:** ✅ Phase 0 Done. Moving to Phase 1+2 in parallel.

### What I did
- Read the synopsis and drafted the implementation plan
- Got user decisions: Gemini (free), PAT for GitHub, no local Docker yet, 1-week deadline, skip voice
- Created the full documentation skeleton:
  - `AGENT.md` — build bible
  - `README.md` — public intro
  - `docs/00_project_brief.md`
  - `docs/01_architecture.md`
  - `docs/02_phase_plan.md` (this is the phase tracker)
  - `docs/03_progress_log.md` (this file)
  - `docs/04_decisions.md`
- Created directory structure: `docs/`, `data/eval/`, `data/prompts/`
- Initialized the git repo, configured local git user (Nancy Kshetrimayum, nancyksh@users.noreply.github.com)
- Created `.gitignore`, `requirements.txt`, `.env.example`, `LICENSE`, `Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml`
- Created `src/__init__.py` package stub
- Added the GitHub remote and **pushed the first commit** (`435721c`) to `https://github.com/nancyksh/TechMentor`
- Secured the PAT: stripped it from the stored remote URL, set up git credential helper (`store` in `~/.git-credentials`)
- Verified `git ls-remote` works with stored credentials

### Next
- Phase 1 — polish architecture doc, add a `docs/05_sequence_diagrams.md` if needed, finalize prompt template placeholders
- Phase 2 — write `src/db/schema.sql`, `src/db/connection.py`, `src/db/dao.py`, `scripts/seed_db.py`, plus unit tests
- Ask the user for the **Gemini API key** so we can wire it into `.env` before Phase 3+ need it

### Blockers / Notes
- Need **Gemini API key** from user (1 min: https://aistudio.google.com/app/apikey) before Phase 3 can run real LLM calls
- HF Spaces account not strictly needed until Phase 10b; we can prepare in parallel
- The `TechMentor_AI_ProjectSynopsis.docx` is committed for historical context; can be removed in a later cleanup commit

### Security note for the user
- A GitHub PAT with `repo` scope and 7-day expiry is in `C:\Users\nancy\.git-credentials` on this machine.
- After the project is done (or earlier if desired), revoke it at https://github.com/settings/tokens

### Cleanup pass (same day)
- Removed the binary `TechMentor_AI_ProjectSynopsis.docx` from the repo — its content is already in `docs/00_project_brief.md`, so the docx was just bloat.
- Tightened `.gitignore` with explicit patterns for `*.docx`, `*.pdf`, `*.pptx`, `*.xlsx`, `data/hf_cache/`, `data/embeddings_cache/`, `data/raw/`, `models_cache/` so future binary reference files and ML caches stay out.
- Pushed as commit `6fa7895`.

### Key validation + standout features added (same day)
- Received Gemini key from user (key stored in `.env` only; never committed. Format prefix: `AQ.Ab` — a valid Google GenAI key format.)
- **Key works** — the format I didn't recognize (`AQ.Ab...`) is a valid Google GenAI key
- Found that `gemini-1.5-flash` is deprecated → switched to `gemini-2.5-flash`
- Found that `google-generativeai` SDK is deprecated → switched to `google-genai` (≥1.0)
- Wrote `scripts/smoke_gemini.py` that auto-discovers the right model for the user's key (handy if they hit rate limits or want to switch)
- Created `.env` (gitignored) with the real key
- Smoke test: **PONG** response from `gemini-2.5-flash` ✅
- **Added 4 standout features to differentiate v1.0** (per user's "make it stand out" request):
  1. 🔬 Live Code Sandbox for DSA
  2. 🗣️💡 Socratic + ELI5 Mode Toggles
  3. 🧠 Weakness Heatmap Dashboard
  4. 🃏 Spaced-Repetition Flashcards (SM-2)
- Updated all docs: `README.md` (Standout Features section), `docs/01_architecture.md` (new components + data flows), `docs/02_phase_plan.md` (4 new sub-phases 5b/6b/7b/8b), `docs/04_decisions.md` (ADR-008 + ADR-009), `AGENT.md` (new SDK troubleshooting)
- Updates landed in commit `e30e14e`
- **Security incident (resolved):** First push was rejected by GitHub's push protection — secret scanner matched a literal key string I had written in the progress log (learning: never write a literal API key into any committed file, even in a log). Also matched a stray `Usersnancy.git-credentials` file created by a PowerShell path-handling bug. Both removed; `.gitignore` tightened with `*git-credentials*`, `*.netrc`, `.ghp_*`, `.github_token` patterns. Commit amended.
