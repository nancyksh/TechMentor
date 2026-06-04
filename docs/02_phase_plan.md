# 02 — Phase Plan & Tracker

> **Current phase is highlighted at the top. The table below is updated after every phase exit.**

## ✅ Current Phase: **0 — Repo & Tooling Bootstrap (DONE)** → moving to **1 — Architecture & Documentation + 2 — Data Layer**

| # | Phase | Deliverable | Status | Completed on |
|---|---|---|---|---|
| **0** | Repo & Tooling Bootstrap | Git init, push to GitHub, `.gitignore`, `requirements.txt`, README skeleton, Dockerfile skeleton, CI lint | ✅ Done | 2026-06-04 |
| 1 | Architecture & Documentation | `docs/01_architecture.md`, `docs/02_phase_plan.md`, `AGENT.md` v1 | 🟢 In Progress | — |
| 2 | Data Layer | SQLite schema (users, sessions, messages, quiz, interview, roadmap), DAO, seed script | 🟢 In Progress | — |
| 3 | NLP Foundation | Sentence-BERT loader, embedding store, retrieval module, prompt templates, intent classifier | ⬜ Pending | — |
| 4 | Supervisor Agent | Intent classification → routing, session context, CrewAI skeleton | ⬜ Pending | — |
| 5 | Subject Agents (OS / DBMS / CN / DSA) | 4 agents w/ domain prompts, eval Q set, ≥80% accuracy | ⬜ Pending | — |
| 6 | Quiz Generation Agent | MCQ + short-answer generation, scoring, history-aware | ⬜ Pending | — |
| 7 | Interview Preparation Agent | Mock interview flow, Q-gen, evaluation rubric, feedback | ⬜ Pending | — |
| 8 | Study Roadmap Agent | Reads session history + scores, outputs prioritized plan | ⬜ Pending | — |
| 9 | Streamlit UI | Single-page app: chat, subject picker, quiz panel, interview panel, roadmap panel, history | ⬜ Pending | — |
| 10a | Testing & QA | Unit + integration tests, fix bugs, CI green | ⬜ Pending | — |
| 10b | Docker & Deploy | Dockerfile, HF Spaces config, secrets, smoke test, live URL | ⬜ Pending | — |

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
