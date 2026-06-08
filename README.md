---
title: TechMentor AI
emoji: 🎓
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8501
pinned: false
---

# TechMentor AI

> Multi-agent intelligent learning and interview assistant for Computer Science students.

[![Phase](https://img.shields.io/badge/Phase-0-blue)](#)
[![Stack](https://img.shields.io/badge/Stack-Streamlit%20%7C%20CrewAI%20%7C%20Gemini%20%7C%20SentenceBERT-green)](#)
[![Deploy](https://img.shields.io/badge/Deploy-HF%20Spaces-yellow)](#)

TechMentor AI is a web-based, multi-agent platform that helps CS students:
- Resolve subject doubts (OS, DBMS, CN, DSA) with **🗣️ Socratic** or **💡 ELI5** teaching modes
- Take auto-generated quizzes
- Practice mock technical interviews with feedback
- Get a personalized study roadmap
- 🔬 **Run DSA code against hidden test cases** in a live sandbox
- 🃏 **Review auto-generated flashcards** on a daily spaced-repetition queue
- 🧠 **Visualize weaknesses** in a live color-coded heatmap

Built with a Supervisor Agent routing queries to specialized agents powered by Google Gemini and Sentence-BERT embeddings. Deployed on Hugging Face Spaces.

## 🌟 What makes it stand out
1. **Live Code Sandbox for DSA** — paste Python, system runs it against hidden tests, reports pass/fail + runtime. *No other "AI tutor" actually executes student code.*
2. **Socratic + ELI5 Modes** — toggle the teaching style per session. Socratic asks guiding questions; ELI5 uses real-world analogies.
3. **Weakness Heatmap** — live, color-coded grid of subjects × topics, computed from your messages, quiz scores, interview feedback, and flashcard recall.
4. **Spaced-Repetition Flashcards (SM-2)** — auto-generated from your weak topics, with a daily review queue that adapts to your recall.

---

## Quickstart

```bash
git clone https://github.com/nancyksh/TechMentor
cd TechMentor
pip install -r requirements.txt
cp .env.example .env       # add your GEMINI_API_KEY
streamlit run src/app.py
```

Open http://localhost:8501.

For the full build guide, see [AGENT.md](./AGENT.md).
For architecture and design decisions, see [docs/](./docs/).

---

## Live Demo

Deployed at: **[https://nanceeeee-techmentor.hf.space](https://nanceeeee-techmentor.hf.space)**

---

## Project Status

See [`docs/02_phase_plan.md`](./docs/02_phase_plan.md) for the live phase tracker and [`docs/03_progress_log.md`](./docs/03_progress_log.md) for the day-by-day build journal.

---

## License

MIT
