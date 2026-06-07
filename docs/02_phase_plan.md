# 02 — Phase Plan & Tracker

> **Current phase is highlighted at the top. The table below is updated after every phase exit.**

## ✅ Current Phase: **0–9 DONE** → moving to **10a — Testing & QA + 10b — Deploy**

| # | Phase | Deliverable | Status | Completed on |
|---|---|---|---|---|
| **0** | Repo & Tooling Bootstrap | Git init, push to GitHub, `.gitignore`, `requirements.txt`, README skeleton, Dockerfile skeleton, CI lint | ✅ Done | 2026-06-04 |
| **1** | Architecture & Documentation | `docs/01_architecture.md`, `docs/02_phase_plan.md`, `AGENT.md` v1 | ✅ Done | 2026-06-04 |
| **2** | Data Layer | SQLite schema (11 tables), DAOs, seed script, **11/11 tests passing** | ✅ Done | 2026-06-04 |
| **3** | NLP Foundation | `google-genai` LLM wrapper, intent classifier (rule-based), prompt templates (11), `smoke_gemini.py`, SM-2 algorithm | ✅ Done | 2026-06-07 |
| **4** | Supervisor Agent | Intent classification → dispatch, session context, message persistence, mode override | ✅ Done | 2026-06-07 |
| **5** | Subject Agents (OS / DBMS / CN / DSA) | 4 agents w/ domain prompts, **Socratic + ELI5 prompt modes** (base agent shared) | ✅ Done | 2026-06-07 |
| **5b** | **Code Sandbox (DSA) — 🌟 STANDOUT** | `src/services/code_runner.py` (subprocess, TLE, test cases), 5 seeded problems | ✅ Done | 2026-06-07 |
| **6** | Quiz Generation Agent | MCQ generation via Gemini, persistence, history | ✅ Done | 2026-06-07 |
| **6b** | **Socratic + ELI5 Mode Toggles — 🌟 STANDOUT** | UI radio toggles in sidebar, prompt swap in subject agents, mode persisted per user | ✅ Done | 2026-06-07 |
| **7** | Interview Preparation Agent | Question generation + answer evaluation (correctness/completeness/clarity), per-question feedback | ✅ Done | 2026-06-07 |
| **7b** | **Flashcard Agent (SM-2) — 🌟 STANDOUT** | Auto-generate cards, SM-2 algorithm (0-5 grade), daily due queue, recall rate tracking | ✅ Done | 2026-06-07 |
| **8** | Study Roadmap Agent | Activity snapshot from DB → LLM 4-week plan, persisted to roadmap_items | ✅ Done | 2026-06-07 |
| **8b** | **Weakness Heatmap — 🌟 STANDOUT** | `src/services/heatmap.py` (weighted aggregation from quiz/flashcard/interview/doubts), Plotly heatmap | ✅ Done | 2026-06-07 |
| **9** | Streamlit UI | 7 pages: Doubt Solver, Quiz, Mock Interview, Code Lab, Flashcards, Dashboard, History | ✅ Done | 2026-06-07 |
| 10a | Testing & QA | **62/62 tests passing**, lint clean, full integration | 🟢 In Progress | — |
| 10b | Docker & Deploy | HF Spaces config, secrets, smoke test, live URL | ⬜ Pending | — |

## 🌟 Standout Features (v1.0 differentiators)
1. **🔬 Live Code Sandbox for DSA** — paste Python, run against hidden tests, get pass/fail + runtime.
2. **🗣️💡 Socratic + ELI5 Mode Toggles** — UI toggle changes agent's teaching style.
3. **🧠 Weakness Heatmap Dashboard** — color-coded live mastery grid across subjects × topics.
4. **🃏 Spaced-Repetition Flashcards (SM-2)** — auto-generated from weak topics, daily review queue.

## Status Legend
- ⬜ Pending
- 🟢 In Progress
- ✅ Done
- ⏸ Blocked
- ⚠️ At Risk

## Tightened 7-Day Schedule

| Day | Phases | Milestone |
|---|---|---|
| 1 | 0 + 1 + 2 | Repo live, DB working, all docs in place |
| 2 | 3 + 4 | Supervisor + intent + retrieval tested |
| 3 | 5 | All 4 subject agents answering correctly |
| 4 | 6 + 7 | Quiz + Interview demo-able |
| 5 | 8 + 9 | Roadmap + full Streamlit UI end-to-end |
| 6 | 10a | Tests green, Docker image builds |
| 7 | 10b | **Public URL live on HF Spaces** |

## Phase Exit Criteria
A phase is "Done" only when:
1. All code committed and pushed
2. Any test for that phase passes locally
3. Progress log entry written in `docs/03_progress_log.md`
4. This file's row updated to ✅ with the date
