"""TechMentor AI — Streamlit Multi-Page App."""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure repo root is on sys.path
_repo = str(Path(__file__).resolve().parent.parent)
if _repo not in sys.path:
    sys.path.insert(0, _repo)

# Load .env before anything else reads env vars
from dotenv import load_dotenv
load_dotenv(Path(_repo) / ".env")

import streamlit as st
from src.db.connection import init_schema, connect
from src.db.dao import UserDAO, SessionDAO, MessageDAO, SettingsDAO, ProblemDAO, CodeRunDAO, QuizDAO
from src.supervisor import Supervisor
from src.services.code_runner import run_code
from src.services.heatmap import build_heatmap
from src.agents.flashcard import get_due_cards, grade_card as grade_flashcard
from src.agents.quiz import generate_quiz
from src.agents.interview import generate_question, evaluate_answer

# ------------------------------------------------------------------
# Page config (must be first Streamlit command)
# ------------------------------------------------------------------
st.set_page_config(page_title="TechMentor AI", page_icon="🎓", layout="wide")

# ------------------------------------------------------------------
# DB init (idempotent)
# ------------------------------------------------------------------
init_schema()


@st.cache_resource
def _get_conn():
    return connect()


_conn = _get_conn()

# ------------------------------------------------------------------
# Session state
# ------------------------------------------------------------------
if "user_id" not in st.session_state:
    st.session_state.user_id = UserDAO.get_or_create_default(_conn)
if "mode" not in st.session_state:
    st.session_state.mode = SettingsDAO.get_mode(_conn, st.session_state.user_id)
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ------------------------------------------------------------------
# Sidebar: navigation + mode toggle
# ------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/graduation-cap.png", width=64)
    st.title("TechMentor AI")
    st.caption("Multi-Agent CS Tutor")
    st.divider()
    page = st.radio(
        "Navigation",
        ["Doubt Solver", "Quiz", "Mock Interview", "Code Lab", "Flashcards", "Dashboard", "History"],
        index=0,
        label_visibility="collapsed",
    )
    st.divider()
    st.subheader("Teaching Mode")
    mode = st.radio(
        "Mode",
        ["default", "socratic", "eli5"],
        index=["default", "socratic", "eli5"].index(st.session_state.mode),
        format_func=lambda m: {
            "default": "Default (direct answer)",
            "socratic": "Socratic (guide me)",
            "eli5": "ELI5 (analogy mode)",
        }[m],
        label_visibility="collapsed",
    )
    if mode != st.session_state.mode:
        st.session_state.mode = mode
        SettingsDAO.set_mode(_conn, st.session_state.user_id, mode)
    st.divider()
    st.caption(f"User ID: {st.session_state.user_id}")
    st.caption("Built with CrewAI · Gemini · Sentence-BERT")

# ------------------------------------------------------------------
# PAGE: Doubt Solver
# ------------------------------------------------------------------
def page_doubt_solver():
    st.header("Doubt Solver")
    st.caption(f"Mode: **{st.session_state.mode}**")

    # Show existing messages
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # New input
    if prompt := st.chat_input("Ask a CS question..."):
        # Display user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Process via Supervisor
        with st.spinner("Thinking..."):
            sup = Supervisor(st.session_state.user_id, _conn)
            response = sup.process(
                prompt,
                session_id=st.session_state.session_id,
                mode_override=st.session_state.mode,
            )
            st.session_state.session_id = sup.session_id

        # Display response
        with st.chat_message("assistant"):
            st.markdown(response.content)

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response.content,
            "intent": response.intent,
            "subject": response.subject,
        })

    # Clear history button
    if st.button("Clear chat"):
        st.session_state.chat_history = []
        st.session_state.session_id = None
        st.rerun()

# ------------------------------------------------------------------
# PAGE: Quiz
# ------------------------------------------------------------------
def page_quiz():
    st.header("Quiz")
    col1, col2, col3 = st.columns(3)
    with col1:
        subject = st.selectbox("Subject", ["OS", "DBMS", "CN", "DSA", "general"], index=0)
    with col2:
        difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"], index=1)
    with col3:
        num_q = st.slider("Questions", 3, 15, 5)

    if st.button("Generate Quiz", type="primary"):
        with st.spinner("Generating quiz..."):
            quiz = generate_quiz(_conn, st.session_state.user_id, subject, None, difficulty, num_q)
        st.session_state.current_quiz = quiz
        st.session_state.quiz_answers = {}

    quiz = st.session_state.get("current_quiz")
    if quiz and quiz.get("questions"):
        st.subheader(f"{subject} Quiz ({difficulty})")
        with st.form("quiz_form"):
            answers = {}
            for i, q in enumerate(quiz["questions"]):
                st.markdown(f"**Q{i+1}.** {q['question']}")
                choices = q.get("choices", [])
                answers[i] = st.radio(f"Q{i+1}", choices, key=f"q{i}", index=None)
                st.write("")
            submitted = st.form_submit_button("Submit")
            if submitted:
                correct = 0
                for i, q in enumerate(quiz["questions"]):
                    correct_idx = q.get("answer_index", 0)
                    chosen = answers.get(i)
                    if chosen is not None:
                        chosen_idx = choices.index(chosen) if chosen in choices else -1
                        is_correct = chosen_idx == correct_idx
                        if is_correct:
                            correct += 1
                        icon = "✅" if is_correct else "❌"
                        st.markdown(f"{icon} **Q{i+1}**: {q.get('explanation', '')}")
                st.success(f"Score: **{correct}/{len(quiz['questions'])}**")
    elif quiz:
        st.info("No questions generated. Try different parameters.")

# ------------------------------------------------------------------
# PAGE: Mock Interview
# ------------------------------------------------------------------
def page_interview():
    st.header("Mock Interview")

    if "interview_state" not in st.session_state:
        st.session_state.interview_state = None

    ist = st.session_state.interview_state

    if ist is None:
        track = st.selectbox("Interview track", ["technical", "hr", "dsa", "mixed"], index=0)
        if st.button("Start Interview", type="primary"):
            with st.spinner("Preparing first question..."):
                q = generate_question(track=track)
            st.session_state.interview_state = {
                "track": track,
                "seq": 1,
                "phase": "answer",
                "current_question": q.get("question", ""),
                "expected_points": q.get("expected_points", []),
                "difficulty": q.get("difficulty", "medium"),
                "history": [],
                "last_eval": None,
                "last_answer": None,
            }
            st.rerun()
    else:
        st.info(f"Track: **{ist['track']}** | Question {ist['seq']}")
        st.markdown(f"### Question {ist['seq']}")
        st.markdown(f"_{ist['current_question']}_")

        phase = ist.get("phase", "answer")

        if phase == "feedback":
            last_eval = ist.get("last_eval") or {}
            last_answer = ist.get("last_answer", "")
            st.markdown(f"**Your answer:** {last_answer}")
            score = last_eval.get("score_correctness", 0)
            st.markdown(f"**Score:** {score:.1f}/1.0")
            st.markdown(f"**Feedback:** {last_eval.get('feedback', '')}")
            missing = last_eval.get("missing_points", [])
            if missing:
                st.markdown("**Missed points:** " + ", ".join(missing))

            if ist["seq"] >= 5:
                if st.button("Finish Interview", type="primary"):
                    st.session_state.interview_state = None
                    st.rerun()
            else:
                if st.button("Next Question", type="primary"):
                    with st.spinner("Generating next question..."):
                        next_q = generate_question(
                            track=ist["track"],
                            seq=ist["seq"] + 1,
                            prev_answer=last_answer,
                            prev_feedback=last_eval.get("feedback", ""),
                        )
                    st.session_state.interview_state = {
                        **st.session_state.interview_state,
                        "seq": ist["seq"] + 1,
                        "phase": "answer",
                        "current_question": next_q.get("question", ""),
                        "expected_points": next_q.get("expected_points", []),
                        "difficulty": next_q.get("difficulty", "medium"),
                        "last_eval": None,
                        "last_answer": None,
                    }
                    st.rerun()
        else:
            answer = st.text_area("Your answer", height=150, key=f"ans_{ist['seq']}")
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Submit Answer", type="primary"):
                    if not answer.strip():
                        st.warning("Please type an answer.")
                    else:
                        eval_result = {}
                        try:
                            with st.spinner("Evaluating..."):
                                eval_result = evaluate_answer(
                                    ist["track"], ist["current_question"],
                                    ist["expected_points"], answer,
                                )
                        except Exception as e:
                            st.error(f"Evaluation failed: {e}")
                            eval_result = {
                                "score_correctness": 0.5,
                                "score_completeness": 0.5,
                                "score_clarity": 0.5,
                                "feedback": f"Evaluation service error: {e}. Your answer was recorded.",
                                "missing_points": [],
                            }

                        new_history = ist.get("history", []) + [{
                            "question": ist["current_question"],
                            "answer": answer,
                            "eval": eval_result,
                        }]
                        st.session_state.interview_state = {
                            **st.session_state.interview_state,
                            "phase": "feedback",
                            "history": new_history,
                            "last_eval": eval_result,
                            "last_answer": answer,
                        }
                        st.rerun()
            with col2:
                if st.button("End Interview"):
                    st.session_state.interview_state = None
                    st.rerun()

# ------------------------------------------------------------------
# PAGE: Code Lab
# ------------------------------------------------------------------
def page_code_lab():
    st.header("Code Lab")
    problems = ProblemDAO.list_all(_conn)
    if not problems:
        st.info("No problems available yet. Run `python scripts/seed_db.py` first.")
        return

    selected = st.selectbox(
        "Choose a problem",
        problems,
        format_func=lambda p: f"[{p['difficulty'].upper()}] {p['title']} ({p['topic']})",
    )
    if not selected:
        return

    problem = ProblemDAO.get(_conn, selected["id"])
    st.subheader(problem["title"])
    st.markdown(problem["prompt"])

    code = st.text_area(
        "Your Python solution",
        value=problem["starter_code"],
        height=300,
        key="code_editor",
    )

    if st.button("Run", type="primary"):
        with st.spinner("Running..."):
            result = run_code(code, problem["test_cases"], time_limit_ms=problem["time_limit_ms"])

        # Persist
        CodeRunDAO.create(
            _conn, st.session_state.user_id, problem["id"], code,
            result.passed, result.total, result.runtime_ms, result.error,
        )

        if result.error and result.passed == 0:
            st.error(f"Runtime error: {result.error}")
        else:
            st.metric("Passed", f"{result.passed}/{result.total}")
            for i, cr in enumerate(result.cases):
                icon = "✅" if cr.passed else "❌"
                st.markdown(f"{icon} **Case {i+1}** (expected: `{cr.expected}`) | got: `{cr.got}` | {cr.runtime_ms}ms")
                if cr.error:
                    st.caption(f"Error: {cr.error}")

    if st.checkbox("Show reference solution"):
        st.code(problem.get("reference", "# No reference available."), language="python")

# ------------------------------------------------------------------
# PAGE: Flashcards
# ------------------------------------------------------------------
def page_flashcards():
    st.header("Flashcards (Spaced Repetition)")

    due = get_due_cards(_conn, st.session_state.user_id)
    st.metric("Cards due today", len(due))

    if not due:
        st.info("No cards due! Generate some from the Doubt Solver or Flashcard command.")
        return

    for card in due[:5]:
        with st.expander(f"Q: {card['front'][:80]}..."):
            st.markdown(f"**Q:** {card['front']}")
            if st.button("Show Answer", key=f"show_{card['id']}"):
                st.markdown(f"**A:** {card['back']}")

            cols = st.columns(6)
            labels = ["0", "1", "2", "3", "4", "5"]
            for i, label in enumerate(labels):
                if cols[i].button(label, key=f"g_{card['id']}_{i}"):
                    result = grade_flashcard(_conn, card["id"], int(label))
                    st.success(f"Grade {label} recorded. Next review: {result['next_review']}")
                    st.rerun()

    if st.button("Generate more cards"):
        st.info("Use the Doubt Solver and say 'generate flashcards on [topic]'")

# ------------------------------------------------------------------
# PAGE: Dashboard (Heatmap)
# ------------------------------------------------------------------
def page_dashboard():
    st.header("Dashboard")

    data = build_heatmap(_conn, st.session_state.user_id)
    subjects = data["subjects"]
    topics = data["topics"]
    grid = data["grid"]

    # Check if there's any data
    total = sum(sum(row) for row in grid)
    if total == 0:
        st.info("No activity data yet. Ask some questions, take quizzes, or review flashcards to see your heatmap.")
        return

    # Build a Plotly heatmap
    import plotly.graph_objects as go
    fig = go.Figure(data=go.Heatmap(
        z=grid,
        x=topics,
        y=subjects,
        colorscale="RdYlGn",
        zmin=0,
        zmax=100,
        text=[[f"{v:.0f}%" for v in row] for row in grid],
        texttemplate="%{text}",
        showscale=True,
        colorbar=dict(title="Mastery %"),
    ))
    fig.update_layout(
        title="Weakness Heatmap",
        xaxis_title="Topics",
        yaxis_title="Subjects",
        height=400,
        xaxis=dict(tickangle=45),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Stats
    col1, col2, col3 = st.columns(3)
    with col1:
        quiz_acc = QuizDAO.accuracy_by_topic(_conn, st.session_state.user_id)
        avg = sum(quiz_acc.values()) / len(quiz_acc) if quiz_acc else 0
        st.metric("Quiz Accuracy", f"{avg:.0%}")
    with col2:
        from src.db.dao import FlashcardDAO
        recall = FlashcardDAO.recall_rate_by_topic(_conn, st.session_state.user_id)
        avg_r = sum(recall.values()) / len(recall) if recall else 0
        st.metric("Flashcard Recall", f"{avg_r:.0%}")
    with col3:
        sessions = SessionDAO.list_for_user(_conn, st.session_state.user_id, limit=100)
        st.metric("Total Sessions", len(sessions))

# ------------------------------------------------------------------
# PAGE: History
# ------------------------------------------------------------------
def page_history():
    st.header("Session History")
    sessions = SessionDAO.list_for_user(_conn, st.session_state.user_id)
    if not sessions:
        st.info("No sessions yet.")
        return

    for s in sessions:
        label = f"{s['kind'].upper()} | {s.get('subject', '—')} | {s['started_at']}"
        with st.expander(label):
            msgs = MessageDAO.list_for_session(_conn, s["id"])
            for m in msgs:
                icon = "🧑" if m["role"] == "user" else "🤖"
                st.markdown(f"{icon} {m['content'][:200]}...")
            if not msgs:
                st.caption("No messages in this session.")

# ------------------------------------------------------------------
# Router
# ------------------------------------------------------------------
PAGE_FNS = {
    "Doubt Solver": page_doubt_solver,
    "Quiz": page_quiz,
    "Mock Interview": page_interview,
    "Code Lab": page_code_lab,
    "Flashcards": page_flashcards,
    "Dashboard": page_dashboard,
    "History": page_history,
}

PAGE_FNS[page]()
