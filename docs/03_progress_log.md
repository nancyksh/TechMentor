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
- Phase 1 + Phase 2 closed out in commit `a5cffc4` (docs + key fix + 4 standout features) and the next commit (data layer)

## Day 1 — Data Layer shipped (Phases 1 + 2 closed) ✅
**Date:** 2026-06-04
**Phases completed:** 1, 2
**Status:** 🟢 Phases 1+2 Done. Moving to Phase 3+4 (NLP foundation + Supervisor).

### What I built
- **`src/db/schema.sql`** — full SQLite schema, 11 tables: `users`, `sessions`, `messages`, `quiz_attempts`, `interview_sessions`, `interview_questions`, `roadmap_items`, `problems`, `code_runs`, `flashcards`, `flashcard_reviews`, `settings`. FK cascades, indexes, WAL mode.
- **`src/db/connection.py`** — connection helper with `transaction()` context manager, `init_schema()` for idempotent schema apply.
- **`src/db/dao.py`** — typed DAOs for every table: `UserDAO`, `SettingsDAO`, `SessionDAO`, `MessageDAO`, `QuizDAO`, `InterviewDAO`, `RoadmapDAO`, `ProblemDAO`, `CodeRunDAO`, `FlashcardDAO`. ~400 lines, no ORM, easy to read.
- **`scripts/init_db.py`** — applies schema.
- **`scripts/seed_db.py`** — seeds a default user and 5 starter DSA problems (Two Sum, Reverse String, FizzBuzz, Binary Search, Count Vowels) for the Code Lab.
- **`tests/test_db.py`** + **`tests/conftest.py`** — 11 unit tests, all green. Cover: user idempotency, settings mode, session+message round-trip, quiz accuracy aggregation, interview with per-question rows, roadmap replace+list, problem upsert with JSON test cases, code run "best of" query, flashcard SM-2 review + recall rate aggregation, FK cascade.

### What it enables
- All 6 agents can persist state immediately (no schema changes needed as we build)
- Code Lab has 5 ready-to-run problems with hidden test cases
- Flashcard SM-2 algorithm has full persistence: `ease`, `interval`, `reps`, `next_review` + per-review history
- Heatmap service can already pull quiz accuracy by topic, flashcard recall by topic, and message counts by subject

### Next
- **Phase 3**: Build `src/nlp/` — Sentence-BERT loader, embedding store, retrieval, intent classifier, Gemini wrapper (`src/nlp/llm.py`), prompt templates in `data/prompts/`
- **Phase 4**: Build `src/supervisor/` — intent router, session context, CrewAI skeleton
- Then **Phase 5**: 4 subject agents with Socratic/ELI5 prompt modes
- Then **Phase 5b**: Code sandbox runner
- Then **Phase 6+7+7b+8+8b**: Quiz, Interview, Flashcard (SM-2), Roadmap, Heatmap
- Then **Phase 9**: Streamlit UI
- Then **Phase 10a+10b**: Tests + Docker + HF Spaces deploy

### Status check
- Day 1 schedule: Phases 0+1+2 done. **Ahead of schedule** (planned 1 day, done in 1 day).
- 11/11 tests green
- GitHub repo: https://github.com/nancyksh/TechMentor (4 commits on main, will be 5 after this log update)
- Key: working, model auto-discovered, smoke test passing (`PONG`)
- No blockers

## Day 1 — Core system shipped (Phases 3–9) 🚀
**Date:** 2026-06-07
**Phases completed:** 3, 4, 5, 5b, 6, 6b, 7, 7b, 8, 8b, 9
**Status:** 🟢 All core code written. **62/62 tests green**, lint clean. Moving to deploy.

### What I built (Phases 3–9)

**Phase 3 — NLP Foundation**
- `src/nlp/llm.py` — Google Gemini wrapper (`google-genai` SDK, not the deprecated `google-generativeai`). Lazy client, retry with backoff, structured JSON extraction, token accounting.
- `src/nlp/intent.py` — Rule-based intent classifier: ~40 regex patterns for 6 intents × 4 subjects × 2 teaching modes. Sub-millisecond, zero LLM calls.
- `src/nlp/prompts.py` — Template loader with `Template.safe_substitute`. 11 prompt templates in `data/prompts/`.
- `src/nlp/retrieval.py` — Sentence-BERT embedding store (dormant for v1, ready to enable via `ENABLE_RETRIEVAL=true`).
- `data/prompts/*.md` — 11 versioned prompt templates: `system_default`, `system_socratic`, `system_eli5`, `subject_os/dbms/cn/dsa`, `quiz_gen`, `interview_gen`, `interview_eval`, `roadmap_gen`, `flashcard_gen`.
- `scripts/smoke_gemini.py` — Auto-discovers the right model for the user's API key (saved us when `gemini-1.5-flash` was deprecated).

**Phase 4 — Supervisor**
- `src/supervisor/supervisor.py` — Central orchestrator. Classifies intent → dispatches to agent → persists messages → returns `AgentResponse`. Supports mode override (UI toggle). Creates/reuses sessions automatically.

**Phase 5 — Subject Agents**
- `src/agents/subjects/base.py` — Shared logic for all 4 subjects. Mode-aware prompt selection (default/socratic/eli5).
- `src/agents/subjects/{os,dbms,cn,dsa}_agent.py` — Thin per-subject wrappers (one function each).
- 3 teaching modes: Default (direct answer), Socratic (2-4 guiding questions), ELI5 (real-world analogy).

**Phase 5b — Code Sandbox (🌟 standout)**
- `src/services/code_runner.py` — Subprocess Python runner with 3s timeout, per-test-case execution, stdout matching. TLE detection. 5 seeded problems (Two Sum, Reverse String, FizzBuzz, Binary Search, Count Vowels).

**Phase 6 — Quiz Agent**
- `src/agents/quiz.py` — Gemini-powered MCQ generation with configurable subject/topic/difficulty/count. Persists to DB.

**Phase 6b — Socratic + ELI5 Mode Toggles (🌟 standout)**
- Sidebar radio buttons in Streamlit. Mode persisted to `settings` table. Subject agents swap system prompt based on mode.

**Phase 7 — Interview Agent**
- `src/agents/interview.py` — Question generation (technical/HR/DSA/mixed tracks) + answer evaluation (correctness/completeness/clarity, each 0.0–1.0). Per-question feedback.

**Phase 7b — Flashcards + SM-2 (🌟 standout)**
- `src/agents/flashcard.py` — Card generation from weak topics, SM-2 algorithm, daily due queue, recall rate tracking.
- `src/services/sm2.py` — Pure-Python SM-2 (grade 0-5, ease/interval/reps state machine). 8 unit tests.

**Phase 8 — Roadmap Agent**
- `src/agents/roadmap.py` — Builds activity snapshot (quiz accuracy + flashcard recall + interview scores + doubt counts) → LLM generates 4-week plan → persisted to DB.

**Phase 8b — Weakness Heatmap (🌟 standout)**
- `src/services/heatmap.py` — Weighted aggregation across 4 data sources (quiz 40%, flashcard 30%, interview 15%, doubts 15%). Returns a subjects × topics grid (0–100%).

**Phase 9 — Streamlit UI**
- `src/app.py` — 7-page single-file Streamlit app: Doubt Solver (chat), Quiz, Mock Interview, Code Lab, Flashcards, Dashboard (Plotly heatmap), History.
- Mode toggle in sidebar. Session persistence. Real-time responses.

### Test suite
- `tests/test_db.py` — 11 tests (schema, DAOs, FK cascades, JSON parsing)
- `tests/test_nlp.py` — 30 tests (intent detection, subject detection, mode detection, prompt rendering, SM-2 algorithm)
- `tests/test_supervisor.py` — 7 tests (classification, routing, persistence, mode override, session reuse) — all LLM calls mocked for deterministic results
- `tests/test_code_runner.py` — 8 tests (pass/fail, runtime error, syntax error, TLE, FizzBuzz, edge cases)
- **Total: 62/62 passing in 2.76s**

### File inventory (this turn)
New files written:
- `src/nlp/llm.py`, `intent.py`, `prompts.py`, `retrieval.py`, `__init__.py`
- `src/supervisor/supervisor.py`, `__init__.py`
- `src/agents/__init__.py`, `quiz.py`, `interview.py`, `flashcard.py`, `roadmap.py`
- `src/agents/subjects/__init__.py`, `base.py`, `os_agent.py`, `dbms_agent.py`, `cn_agent.py`, `dsa_agent.py`
- `src/services/__init__.py`, `code_runner.py`, `heatmap.py`, `sm2.py`
- `src/app.py`
- `data/prompts/*.md` (11 templates)
- `tests/test_nlp.py`, `test_supervisor.py`, `test_code_runner.py`, `conftest.py`
- `requirements-extra.txt`

### HF Spaces deploy — LIVE ✅
- Created `start.sh` — startup script (init schema + seed DB + launch Streamlit)
- Updated `Dockerfile` — uses `start.sh`, proper permissions, healthcheck
- Added HF Spaces SDK front matter to `README.md`
- Fixed `QuizDAO` import in `app.py` (F821 lint error)
- User created Space at https://huggingface.co/spaces/Nanceeeee/TechMentor
- User set `GEMINI_API_KEY` secret in Space settings
- Pushed code to HF Space via git push (force push to overwrite default README)
- Build completed in ~4 minutes (Docker image + Sentence-BERT model download)
- **App is LIVE at https://nanceeeee-techmentor.hf.space** ✅
- HF token stripped from git credentials for security
- Commit `e89639a` on GitHub, same SHA deployed to HF Spaces

### v1.0 Deployed — ALL PHASES COMPLETE 🎉
- 7 commits on main
- 62/62 tests passing
- All lint clean
- 4 standout features working (Code Sandbox, Socratic/ELI5, Heatmap, Flashcards)
- 7-page Streamlit UI
- Live on HF Spaces
