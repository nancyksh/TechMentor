# 00 — Project Brief

## Title
**TechMentor AI: A Multi-Agent Intelligent Learning and Interview Assistant for Computer Science Education**

## Author & Context
- **Student:** Nancy Kshetrimayum (25ETCS126011)
- **Program:** M.Tech — Artificial Intelligence and Machine Learning, II Semester
- **Guide:** Dr. Narendra Babu
- **University:** M.S. Ramaiah University of Applied Sciences
- **Year:** 2026

## Problem Statement
CS students (UG/PG) struggle to find:
1. Interactive, subject-specific, context-aware academic help
2. Real-time assessment of their understanding
3. Realistic technical interview practice for placements/GATE

Static textbooks, recorded lectures, and general-purpose chatbots do not address these gaps.

## Solution
A web-based, multi-agent intelligent platform that provides:
- **Doubt solving** across OS, DBMS, CN, DSA
- **Auto-generated quizzes** (MCQ + short answer) for self-assessment
- **Mock technical interviews** with structured feedback
- **Personalized study roadmaps** based on interaction history

## Primary Objectives
1. Multi-agent architecture with a Supervisor Agent routing user queries
2. Subject-specific agents for OS, DBMS, CN, DSA
3. Quiz Generation Agent for dynamic MCQs
4. Interview Preparation Agent with feedback
5. Study Roadmap Agent using session history
6. Public deployment on Hugging Face Spaces

## Out of Scope (v1)
- Voice input/output (STT/TTS)
- LMS (Moodle) integration
- Multilingual support
- RL-based roadmap optimization

## Success Criteria
- Answers to 20-question eval set per subject achieve ≥80% factual correctness (human spot-check)
- Quiz and Interview agents produce coherent, evaluable outputs
- End-to-end demo on HF Spaces runs without errors for a sample session
- README and AGENT.md sufficient for a new contributor to run the project
