# 01 — Architecture

## High-Level Diagram

```
┌────────────────────────────────────────────────────────────┐
│                  Streamlit Frontend (src/app.py)            │
│   Chat | Quiz | Interview | Roadmap | History              │
└──────────────────────────┬─────────────────────────────────┘
                           │  user message + session ctx
                           ▼
┌────────────────────────────────────────────────────────────┐
│              Supervisor Agent (src/supervisor)              │
│   • Intent classifier (rule + small ML hybrid)              │
│   • Session context manager                                │
│   • Routes to one of 6 specialized agents                  │
└──┬──────────┬──────────┬──────────┬──────────┬─────────────┘
   ▼          ▼          ▼          ▼          ▼
┌──────┐  ┌──────┐   ┌──────┐  ┌──────┐   ┌──────────┐
│  OS  │  │ DBMS │   │  CN  │  │ DSA  │   │  Quiz /  │
│Agent │  │Agent │   │Agent │  │Agent │   │Interview │
└──┬───┘  └──┬───┘   └──┬───┘  └──┬───┘   │ Roadmap  │
   │         │          │         │       └────┬─────┘
   ▼         ▼          ▼         ▼            ▼
┌────────────────────────────────────────────────────────────┐
│           NLP Foundation (src/nlp)                          │
│  • Sentence-BERT embeddings (all-MiniLM-L6-v2)              │
│  • Cosine retrieval over domain KB snippets                 │
│  • Prompt templates (data/prompts/*.md)                    │
└──────────────────────────┬─────────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────────┐
│                 LLM Layer (Gemini)                          │
│   google-generativeai SDK → gemini-1.5-flash                │
└──────────────────────────┬─────────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────────┐
│               Persistence (src/db) — SQLite                 │
│   Tables: users, sessions, messages, quiz_attempts,         │
│           interview_sessions, roadmap_items                 │
└────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### Streamlit Frontend
- Single-page app with sidebar navigation: **Doubt Solver** | **Quiz** | **Mock Interview** | **Roadmap** | **Code Lab** | **Flashcards** | **Dashboard** | **History**
- Holds `st.session_state` for current user, session id, message history
- Calls into Supervisor via a thin service layer
- **Mode toggles** (top bar): `Default` · `🗣️ Socratic` · `💡 ELI5` — change subject-agent prompt at runtime

### Supervisor Agent
- Receives raw user input + session context
- Runs **intent classifier** → returns `{intent, subject, mode}`
- Routes to the right specialized agent, passing context
- Returns the agent's response back to the UI

### Specialized Agents (6)
- **OS / DBMS / CN / DSA Agents** — subject doubt solving, retrieval-augmented, prompt swap on Socratic/ELI5 mode
- **Quiz Agent** — generates MCQs, evaluates answers
- **Interview Agent** — drives mock interview, evaluates response
- **Roadmap Agent** — reads session history, produces prioritized plan
- **Flashcard Agent** *(v1.0 standout)* — generates flashcards from weak topics, runs SM-2 spaced repetition

### Standout Services (v1.0 differentiators)
- **`src/services/code_runner.py`** — subprocess-based Python sandbox (3-sec timeout, hidden test cases, returns pass/fail + runtime + memory). THE killer demo for DSA.
- **`src/services/heatmap.py`** — aggregates mastery across `messages`, `quiz_attempts`, `interview_sessions`; emits a (subject, topic) → score grid.
- **`src/services/sm2.py`** — pure-Python SM-2 spaced repetition algorithm. No LLM needed.

### Supervisor Agent
- Receives raw user input + session context
- Runs **intent classifier** → returns `{intent, subject, mode}`
- Routes to the right specialized agent, passing context
- Returns the agent's response back to the UI

### Specialized Agents (6)
- **OS / DBMS / CN / DSA Agents** — subject doubt solving, retrieval-augmented
- **Quiz Agent** — generates MCQs, evaluates answers
- **Interview Agent** — drives mock interview, evaluates response
- **Roadmap Agent** — reads session history, produces prioritized plan

### NLP Foundation
- Loads Sentence-BERT once at app start (singleton)
- Embeds KB snippets + user queries
- Cosine similarity top-k retrieval
- Prompt templates live in `data/prompts/*.md` for easy iteration

### Persistence
- SQLite file at `data/techmentor.db`
- DAOs in `src/db/` with a thin, type-safe API
- Schema migrations via `scripts/migrate.py` (sequential numbered SQL files)

## Data Flow — Doubt Solving
1. User types a question in Streamlit
2. Supervisor classifies intent = `DOUBT`, subject = `OS`
3. OS agent's prompt is built: `{system_prompt} + {retrieved_snippets} + {user_query}`
4. Gemini returns the answer
5. Message + metadata saved to `messages` table
6. Answer rendered in UI

## Data Flow — Quiz
1. User selects subject + difficulty + count
2. Quiz Agent generates N MCQs (JSON) via Gemini
3. Streamlit renders them
4. User submits → Quiz Agent scores → results saved to `quiz_attempts`

## Data Flow — Mock Interview
1. User selects track (HR / Technical / DSA coding)
2. Interview Agent generates first question
3. Streamlit shows question, captures answer
4. Agent evaluates: `{correctness, completeness, clarity, score}`, returns feedback
5. Next question is generated conditioned on previous answers
6. Session summary saved to `interview_sessions`

## Data Flow — Study Roadmap
1. User clicks "Generate Roadmap"
2. Roadmap Agent reads `messages` + `quiz_attempts` + `interview_sessions`
3. LLM produces a structured weekly plan (JSON) with weak areas prioritized
4. Plan saved to `roadmap_items` + rendered as Streamlit cards/timeline

## Data Flow — Code Sandbox (DSA)
1. User picks a problem in the **Code Lab** page
2. User pastes Python solution → clicks **Run**
3. `code_runner.py` writes the code to a temp file, runs `subprocess.run([sys.executable, ...], timeout=3, capture_output=True)`
4. Stdout is matched against a list of hidden test cases (`assert`-style)
5. Result `{passed, total, runtime_ms, error}` is returned to the UI and saved to `code_runs` table

## Data Flow — Spaced Repetition Flashcards
1. Flashcard Agent reads recent weak topics from `quiz_attempts`
2. LLM generates 1-3 cards per weak topic (front = question, back = concise answer)
3. Cards saved to `flashcards` with initial SM-2 state (`ease=2.5, interval=0, reps=0`)
4. Daily review queue: cards where `next_review <= today` ordered by overdue
5. User grades recall 0-5; SM-2 updates `ease`, `interval`, `reps`, `next_review`
6. Card state saved to `flashcard_reviews` (history of every review)

## Data Flow — Weakness Heatmap
1. `heatmap.py` aggregates across `messages` (intent=DOUBT count per topic), `quiz_attempts` (accuracy per topic), `interview_sessions` (avg score per topic), `flashcard_reviews` (recall rate per card → topic)
2. Returns a grid: rows = subjects (OS/DBMS/CN/DSA/Interview), cols = topics, cells = mastery % (0-100)
3. UI renders as a color-coded `plotly` heatmap (red → yellow → green)

## Design Tradeoffs

| Decision | Why |
|---|---|
| CrewAI for orchestration | Synopsis-mandated; lighter than full LangChain for our scope |
| Gemini (not OpenAI) | User-requested; free tier, generous limits |
| `google-genai` SDK (not deprecated `google-generativeai`) | The old SDK was retired by Google; the new SDK uses `gemini-2.5-flash`+ and `client.models.generate_content(...)` |
| Sentence-BERT `all-MiniLM-L6-v2` | Small (80 MB), fast, accurate enough for short snippets |
| SQLite | Zero-setup, fits single-user, single-semester scope |
| HF Spaces Docker | Free CPU, public URL, perfect for student demo |
| No RAG KB (v1) | User chose to rely on LLM knowledge to ship in 1 week |
| Subprocess sandbox (not Docker-in-Docker) for code execution | Zero extra infra, 3-sec timeout = safe, no Docker needed for the code runner itself |
| SM-2 (not FSRS) for spaced repetition | Battle-tested, 5-line implementation, fits v1 scope |
