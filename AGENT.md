# AGENT.md — TechMentor AI Build Bible

> **Single source of truth for building, running, and deploying TechMentor AI.**
> Any contributor (or future you) should be able to rebuild the entire project by following this file top-to-bottom.

---

## 0. What is TechMentor AI?

A multi-agent intelligent learning and interview assistant for Computer Science students.

Students can:
- Ask doubts in OS / DBMS / CN / DSA and get context-aware answers
- Take auto-generated quizzes (MCQ + short answer)
- Practice mock technical interviews and get feedback
- Receive personalized study roadmaps based on their activity

---

## 1. Tech Stack (pinned)

| Layer | Technology | Version |
|---|---|---|
| Language | Python | 3.11+ (tested on 3.13.5) |
| Frontend | Streamlit | ≥1.36 |
| Agent orchestration | CrewAI | ≥0.86 |
| LLM | Google Gemini (`gemini-2.5-flash` / `gemini-2.5-pro` / `gemini-2.0-flash`) via `google-genai` | ≥1.0 |
| Embeddings | Sentence-Transformers `all-MiniLM-L6-v2` | latest |
| Vector store | NumPy cosine (in-memory) | bundled |
| Database | SQLite (stdlib) | 3 |
| Testing | pytest | ≥8 |
| Lint | ruff | latest |
| CI | GitHub Actions | ubuntu-latest |
| Container | Docker (multi-stage, `python:3.11-slim`) | — |
| Deploy | Hugging Face Spaces (Docker SDK) | — |

---

## 2. Repository Layout

```
TechMentor/
├── AGENT.md                  ← this file
├── README.md                 public intro
├── LICENSE
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
├── docs/
│   ├── 00_project_brief.md
│   ├── 01_architecture.md
│   ├── 02_phase_plan.md
│   ├── 03_progress_log.md
│   └── 04_decisions.md
├── src/
│   ├── app.py                Streamlit entrypoint
│   ├── config.py             env + paths
│   ├── supervisor/           intent classifier + router
│   ├── agents/               subject, quiz, interview, roadmap
│   ├── nlp/                  embeddings, retrieval, prompts
│   ├── db/                   schema, DAO, migrations
│   └── utils/                logging, helpers
├── data/
│   ├── eval/                 evaluation Q sets (jsonl)
│   └── prompts/              versioned prompt templates
├── scripts/
│   ├── seed_db.py
│   └── smoke.py
└── tests/
    ├── test_db.py
    ├── test_intent.py
    ├── test_subjects.py
    └── test_e2e.py
```

---

## 3. Environment Variables

Copy `.env.example` to `.env` and fill in:

```env
# LLM
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-1.5-flash

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# App
APP_DB_PATH=./data/techmentor.db
APP_LOG_LEVEL=INFO
```

`.env` is **gitignored** — never commit keys. On HF Spaces, add the same vars to **Settings → Secrets**.

---

## 4. Run Locally (without Docker)

```bash
# 1. Create venv
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 2. Install deps
pip install -r requirements.txt

# 3. Seed DB
python scripts/seed_db.py

# 4. Launch Streamlit
streamlit run src/app.py
# open http://localhost:8501
```

---

## 5. Run with Docker (optional, when Docker is installed)

```bash
docker compose up --build
# open http://localhost:8501
```

The `Dockerfile` uses a multi-stage build on `python:3.11-slim`, runs as non-root, exposes `8501`.

---

## 6. Deploy to Hugging Face Spaces

HF Spaces with **Docker SDK** is the production target. Steps:

1. Create a Space: https://huggingface.co/new-space → **Docker** → blank.
2. Add a Git remote: `git remote add hf https://huggingface.co/spaces/nancyksh/TechMentor`.
3. Set secrets: Space → **Settings → Variables and secrets** → add `GEMINI_API_KEY`.
4. Push: `git push hf main`.
5. The Space builds the Dockerfile and serves on `https://nancyksh-techmentor.hf.space`.

---

## 7. Testing

```bash
pytest -v
pytest --cov=src tests/   # with coverage
```

Test layers:
- **Unit** — DB DAO, intent classifier, prompt builders.
- **Integration** — each agent against a small LLM-stubbed fixture.
- **E2E** — full Streamlit session simulated via `streamlit.testing.v1`.

---

## 8. CI

`.github/workflows/ci.yml` runs on every push to `main` / PR:
1. Checkout
2. Setup Python 3.11
3. `pip install -r requirements.txt`
4. `ruff check .`
5. `pytest -q`

---

## 9. Branching & Release

- `main` — always deployable
- `dev` — integration branch
- `phase/N-short-name` — feature work
- One squash-merge PR per phase
- Tag releases: `v0.1.0` (after Phase 5), `v0.5.0` (after Phase 9), `v1.0.0` (after Phase 10)

---

## 10. Troubleshooting

| Problem | Fix |
|---|---|
| `google-genai` 401 / 403 | Key missing/wrong/restricted. Re-check `.env` / HF Space secrets. |
| `404 NOT_FOUND models/gemini-1.5-flash` | The 1.5 model line was retired. Use `gemini-2.5-flash` (or `gemini-2.0-flash`). Run `python scripts/smoke_gemini.py` to auto-discover allowed models. |
| `sentence-transformers` download fails | Pre-download model, set `HF_HOME` to a writable dir, or pass `cache_folder=`. |
| Streamlit `SessionState` warnings | Use `st.session_state` (Streamlit ≥1.28). |
| HF Space build OOM | Switch to `cpu-basic` (16 GB) or reduce model size. |
| Slow first response | Gemini cold start ~1-2s; consider warming up at app boot. |

---

## 11. Roadmap beyond v1

- Voice (STT/TTS)
- Multilingual (Indic languages)
- RL-based roadmap optimization
- LMS (Moodle) integration
- LangChain agents with memory + tools

See `docs/04_decisions.md` for design tradeoffs.
