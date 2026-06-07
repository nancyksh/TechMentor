-- ============================================================
-- TechMentor AI — SQLite schema v1
-- Apply with:  python scripts/init_db.py
-- Re-apply safely: drop file at $APP_DB_PATH and re-run.
-- ============================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- ---------- Users (single-user v1, table kept for future) ----------
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    display_name  TEXT    NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ---------- Generic sessions (chat / quiz / interview) ----------
CREATE TABLE IF NOT EXISTS sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kind        TEXT    NOT NULL CHECK (kind IN ('chat','quiz','interview','roadmap','code','flashcards')),
    subject     TEXT,                                -- OS / DBMS / CN / DSA / NULL
    topic       TEXT,
    started_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    ended_at    TEXT
);
CREATE INDEX IF NOT EXISTS idx_sessions_user_kind ON sessions(user_id, kind);

-- ---------- Chat messages (doubts, code questions) ----------
CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role        TEXT    NOT NULL CHECK (role IN ('user','assistant','system')),
    content     TEXT    NOT NULL,
    intent      TEXT,                                -- DOUBT / QUIZ / INTERVIEW / ROADMAP / CODE
    subject     TEXT,
    mode        TEXT,                                -- default | socratic | eli5
    tokens      INTEGER,
    latency_ms  INTEGER,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_subject ON messages(subject);

-- ---------- Quiz attempts ----------
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id  INTEGER REFERENCES sessions(id) ON DELETE SET NULL,
    subject     TEXT    NOT NULL,
    topic       TEXT,
    difficulty  TEXT    NOT NULL CHECK (difficulty IN ('easy','medium','hard')),
    num_questions INTEGER NOT NULL,
    score       INTEGER NOT NULL,                    -- correct count
    total       INTEGER NOT NULL,
    details     TEXT,                                -- JSON: questions, choices, user answers
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_quiz_user_subject ON quiz_attempts(user_id, subject);

-- ---------- Interview sessions + per-question rows ----------
CREATE TABLE IF NOT EXISTS interview_sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id  INTEGER REFERENCES sessions(id) ON DELETE SET NULL,
    track       TEXT    NOT NULL CHECK (track IN ('hr','technical','dsa','mixed')),
    started_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    ended_at    TEXT,
    avg_score   REAL
);
CREATE INDEX IF NOT EXISTS idx_interview_user ON interview_sessions(user_id);

CREATE TABLE IF NOT EXISTS interview_questions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    interview_id INTEGER NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    seq         INTEGER NOT NULL,
    question    TEXT    NOT NULL,
    answer      TEXT,
    score_correctness   REAL,
    score_completeness  REAL,
    score_clarity       REAL,
    feedback   TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_iq_interview ON interview_questions(interview_id);

-- ---------- Roadmap ----------
CREATE TABLE IF NOT EXISTS roadmap_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    week        INTEGER NOT NULL,                    -- 1-based
    subject     TEXT    NOT NULL,
    topic       TEXT    NOT NULL,
    priority    INTEGER NOT NULL,                    -- 1 = highest
    rationale   TEXT,
    resources   TEXT,                                -- JSON array of {title,url,kind}
    completed   INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_roadmap_user ON roadmap_items(user_id, week);

-- ---------- DSA problems (for Code Lab) ----------
CREATE TABLE IF NOT EXISTS problems (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    slug            TEXT    NOT NULL UNIQUE,
    title           TEXT    NOT NULL,
    subject         TEXT    NOT NULL DEFAULT 'DSA',
    topic           TEXT    NOT NULL,
    difficulty      TEXT    NOT NULL CHECK (difficulty IN ('easy','medium','hard')),
    prompt          TEXT    NOT NULL,                -- markdown
    starter_code    TEXT    NOT NULL,
    test_cases      TEXT    NOT NULL,                -- JSON: [{"stdin":"...","expected":"..."}]
    reference       TEXT,                            -- reference solution
    time_limit_ms   INTEGER NOT NULL DEFAULT 3000,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_problems_topic ON problems(topic, difficulty);

-- ---------- Code runs (Code Lab) ----------
CREATE TABLE IF NOT EXISTS code_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    problem_id  INTEGER NOT NULL REFERENCES problems(id) ON DELETE CASCADE,
    session_id  INTEGER REFERENCES sessions(id) ON DELETE SET NULL,
    code        TEXT    NOT NULL,
    passed      INTEGER NOT NULL,
    total       INTEGER NOT NULL,
    runtime_ms  INTEGER,
    error       TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_code_runs_user ON code_runs(user_id, problem_id);

-- ---------- Flashcards (SM-2) ----------
CREATE TABLE IF NOT EXISTS flashcards (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject     TEXT    NOT NULL,
    topic       TEXT    NOT NULL,
    front       TEXT    NOT NULL,
    back        TEXT    NOT NULL,
    ease        REAL    NOT NULL DEFAULT 2.5,
    interval    INTEGER NOT NULL DEFAULT 0,           -- days
    reps        INTEGER NOT NULL DEFAULT 0,
    next_review TEXT    NOT NULL DEFAULT (date('now')),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_flashcards_due ON flashcards(user_id, next_review);

CREATE TABLE IF NOT EXISTS flashcard_reviews (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id         INTEGER NOT NULL REFERENCES flashcards(id) ON DELETE CASCADE,
    reviewed_at     TEXT    NOT NULL DEFAULT (datetime('now')),
    grade           INTEGER NOT NULL CHECK (grade BETWEEN 0 AND 5),
    prev_ease       REAL    NOT NULL,
    prev_interval   INTEGER NOT NULL,
    new_ease        REAL    NOT NULL,
    new_interval    INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_fcr_card ON flashcard_reviews(card_id);

-- ---------- Settings (per-user UI prefs incl. mode toggles) ----------
CREATE TABLE IF NOT EXISTS settings (
    user_id     INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    default_mode TEXT    NOT NULL DEFAULT 'default',  -- default | socratic | eli5
    ui_json     TEXT,                                -- free-form UI prefs
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
