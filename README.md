# TechMentor AI

> Multi-agent intelligent learning and interview assistant for Computer Science students.

[![Phase](https://img.shields.io/badge/Phase-0-blue)](#)
[![Stack](https://img.shields.io/badge/Stack-Streamlit%20%7C%20CrewAI%20%7C%20Gemini%20%7C%20SentenceBERT-green)](#)
[![Deploy](https://img.shields.io/badge/Deploy-HF%20Spaces-yellow)](#)

TechMentor AI is a web-based, multi-agent platform that helps CS students:
- Resolve subject doubts (OS, DBMS, CN, DSA)
- Take auto-generated quizzes
- Practice mock technical interviews with feedback
- Get a personalized study roadmap

Built with a Supervisor Agent routing queries to specialized agents powered by Google Gemini and Sentence-BERT embeddings. Deployed on Hugging Face Spaces.

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

Deployed at: **https://nancyksh-techmentor.hf.space** *(updated in Phase 10)*

---

## Project Status

See [`docs/02_phase_plan.md`](./docs/02_phase_plan.md) for the live phase tracker and [`docs/03_progress_log.md`](./docs/03_progress_log.md) for the day-by-day build journal.

---

## License

MIT
