"""NLP module tests — intent classifier, prompts, SM-2."""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.nlp.intent import classify
from src.nlp.prompts import render, render_strict, list_prompts
from src.services.sm2 import review, CardState
from datetime import date


# ============================================================
# Intent classifier — intent detection
# ============================================================

class TestIntentDetection:
    def test_doubt_os(self):
        cls = classify("What is a deadlock?")
        assert cls.intent == "DOUBT"
        assert cls.subject == "OS"

    def test_doubt_dbms(self):
        cls = classify("Explain 3NF normalization in DBMS")
        assert cls.subject == "DBMS"

    def test_doubt_cn(self):
        cls = classify("What is the OSI model?")
        assert cls.subject == "CN"

    def test_doubt_dsa(self):
        cls = classify("How does binary search work?")
        assert cls.subject == "DSA"

    def test_quiz_intent(self):
        cls = classify("Give me a quiz on Operating Systems")
        assert cls.intent == "QUIZ"
        assert cls.subject == "OS"

    def test_quiz_mcq(self):
        cls = classify("Generate 5 MCQs on DBMS")
        assert cls.intent == "QUIZ"
        assert cls.subject == "DBMS"

    def test_interview_intent(self):
        cls = classify("I want a mock interview")
        assert cls.intent == "INTERVIEW"

    def test_interview_hr(self):
        cls = classify("HR interview questions")
        assert cls.intent == "INTERVIEW"

    def test_roadmap_intent(self):
        cls = classify("Give me a study roadmap for GATE")
        assert cls.intent == "ROADMAP"

    def test_roadmap_where_start(self):
        cls = classify("Where should I start studying for OS?")
        assert cls.intent == "ROADMAP"
        assert cls.subject == "OS"

    def test_code_intent(self):
        cls = classify("Run my code")
        assert cls.intent == "CODE"

    def test_flashcard_intent(self):
        cls = classify("Show me flashcards for DBMS")
        assert cls.intent == "FLASHCARD"
        assert cls.subject == "DBMS"

    def test_chitchat_empty(self):
        cls = classify("")
        assert cls.intent == "CHITCHAT"


# ============================================================
# Intent classifier — subject detection
# ============================================================

class TestSubjectDetection:
    def test_os_keywords(self):
        for kw in ["scheduling", "deadlock", "semaphore", "virtual memory", "processes"]:
            cls = classify(f"Tell me about {kw}")
            assert cls.subject == "OS", f"Failed for keyword: {kw}"

    def test_dbms_keywords(self):
        for kw in ["SQL", "normalization", "ACID", "indexing", "foreign key"]:
            cls = classify(f"Explain {kw}")
            assert cls.subject == "DBMS", f"Failed for keyword: {kw}"

    def test_cn_keywords(self):
        for kw in ["TCP", "routing", "HTTP", "DNS", "subnetting"]:
            cls = classify(f"What is {kw}?")
            assert cls.subject == "CN", f"Failed for keyword: {kw}"

    def test_dsa_keywords(self):
        for kw in ["binary search", "linked list", "graph", "sorting", "dynamic programming"]:
            cls = classify(f"Explain {kw}")
            assert cls.subject == "DSA", f"Failed for keyword: {kw}"

    def test_no_subject_when_no_keyword(self):
        cls = classify("Hello")
        assert cls.subject is None  # or whatever the default is


# ============================================================
# Intent classifier — mode detection
# ============================================================

class TestModeDetection:
    def test_socratic_mode(self):
        cls = classify("What is a deadlock? Don't just tell me.")
        assert cls.mode == "socratic"

    def test_eli5_mode(self):
        cls = classify("Explain like I'm 5: what is SQL?")
        assert cls.mode == "eli5"

    def test_eli5_analogy(self):
        cls = classify("Use an analogy to explain virtual memory")
        assert cls.mode == "eli5"

    def test_default_mode(self):
        cls = classify("What is a semaphore?")
        assert cls.mode == "default"

    def test_combined_socratic_subject(self):
        cls = classify("Guide me through normalization in DBMS")
        assert cls.mode == "socratic"
        assert cls.subject == "DBMS"


# ============================================================
# Prompt rendering
# ============================================================

class TestPromptRendering:
    def test_list_prompts_not_empty(self):
        prompts = list_prompts()
        assert len(prompts) >= 8
        assert "system_default" in prompts

    def test_render_subject_os(self):
        text = render("subject_os", question="What is a deadlock?", topic="deadlocks")
        assert "Operating Systems" in text or "OS" in text
        assert "deadlock" in text.lower()

    def test_render_quiz_gen(self):
        text = render("quiz_gen", num_questions=5, subject="OS", topic="scheduling", difficulty="medium")
        assert "5" in text
        assert "OS" in text

    def test_render_strict_raises_on_missing_var(self):
        import pytest
        with pytest.raises(KeyError):
            render_strict("quiz_gen")  # missing required vars


# ============================================================
# SM-2 algorithm
# ============================================================

class TestSM2:
    def test_initial_state(self):
        s = CardState()
        assert s.ease == 2.5
        assert s.interval == 0
        assert s.reps == 0

    def test_forgot_resets(self):
        s, next_d = review(CardState(), grade=0, today=date(2026, 1, 1))
        assert s.reps == 0
        assert s.interval == 1
        assert next_d == date(2026, 1, 2)

    def test_first_correct(self):
        s, next_d = review(CardState(), grade=4, today=date(2026, 1, 1))
        assert s.reps == 1
        assert s.interval == 1
        assert s.ease > 2.4  # should have increased slightly
        assert next_d == date(2026, 1, 2)

    def test_second_correct(self):
        s1, _ = review(CardState(), grade=4, today=date(2026, 1, 1))
        s2, next_d = review(s1, grade=4, today=date(2026, 1, 2))
        assert s2.reps == 2
        assert s2.interval == 6
        assert next_d == date(2026, 1, 8)

    def test_third_correct_grows_interval(self):
        s1, _ = review(CardState(), grade=4, today=date(2026, 1, 1))
        s2, _ = review(s1, grade=4, today=date(2026, 1, 2))
        s3, next_d = review(s2, grade=4, today=date(2026, 1, 8))
        assert s3.reps == 3
        assert s3.interval == round(6 * s2.ease)
        assert next_d > date(2026, 1, 8)

    def test_ease_decreases_on_low_passing_grade(self):
        s1, _ = review(CardState(), grade=4, today=date(2026, 1, 1))
        s2, _ = review(s1, grade=4, today=date(2026, 1, 2))
        s3, _ = review(s2, grade=4, today=date(2026, 1, 8))
        ease_before = s3.ease
        s4, _ = review(s3, grade=3, today=date(2026, 1, 30))
        assert s4.ease < ease_before  # ease decreased on grade=3 (passing but low)
        assert s4.reps == 4
        assert s4.interval > 0

    def test_forget_does_not_change_ease(self):
        s1, _ = review(CardState(), grade=4, today=date(2026, 1, 1))
        ease_before = s1.ease
        s2, _ = review(s1, grade=2, today=date(2026, 1, 2))
        assert s2.ease == ease_before  # grade < 3: ease unchanged
        assert s2.reps == 0
        assert s2.interval == 1

    def test_ease_minimum_1_3(self):
        s = CardState(ease=1.3)
        s2, _ = review(s, grade=0, today=date(2026, 1, 1))
        # grade < 3 doesn't change ease
        assert s2.ease >= 1.3

    def test_invalid_grade_raises(self):
        import pytest
        with pytest.raises(ValueError):
            review(CardState(), grade=6)
        with pytest.raises(ValueError):
            review(CardState(), grade=-1)
