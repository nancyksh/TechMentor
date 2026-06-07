"""Supervisor — the central orchestrator for TechMentor AI.

Receives a user message, classifies its intent via the rule-based classifier,
then dispatches to the appropriate agent. Manages session context and persists
messages to the DB.

Public API:
    sup = Supervisor(user_id=1, conn=conn)
    response = sup.process("What is deadlock?")
    # -> {"role": "assistant", "content": "...", "intent": "DOUBT", "subject": "OS", ...}
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

from src.nlp.intent import classify, Classification
from src.db.dao import SessionDAO, MessageDAO, SettingsDAO


@dataclass
class AgentResponse:
    content: str
    intent: str
    subject: str | None = None
    mode: str = "default"
    topic: str | None = None
    meta: dict[str, Any] | None = None  # agent-specific extra data

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "role": "assistant",
            "content": self.content,
            "intent": self.intent,
            "subject": self.subject,
            "mode": self.mode,
            "topic": self.topic,
        }
        if self.meta:
            d["meta"] = self.meta
        return d


class Supervisor:
    def __init__(self, user_id: int, conn: sqlite3.Connection):
        self.user_id = user_id
        self.conn = conn
        self._session_id: int | None = None
        self._mode: str = SettingsDAO.get_mode(conn, user_id)

    @property
    def session_id(self) -> int | None:
        return self._session_id

    def process(
        self,
        message: str,
        *,
        session_id: int | None = None,
        mode_override: str | None = None,
    ) -> AgentResponse:
        """Classify the message, dispatch to the right agent, persist, return."""

        # 1. Determine mode (explicit override > stored > default)
        mode = mode_override or self._mode

        # 2. Classify intent, subject, mode from the message itself
        cls = classify(message, default_mode=mode)

        # 3. Use explicit override if provided (UI toggle)
        if mode_override and mode_override in ("default", "socratic", "eli5"):
            cls.mode = mode_override

        # 4. Create or re-use a session
        if session_id:
            self._session_id = session_id
        if not self._session_id:
            kind = _intent_to_kind(cls.intent)
            self._session_id = SessionDAO.create(
                self.conn, self.user_id, kind, subject=cls.subject, topic=cls.topic
            )

        # 5. Persist the user message
        MessageDAO.add(
            self.conn,
            self._session_id,
            "user",
            message,
            intent=cls.intent,
            subject=cls.subject,
            mode=cls.mode,
        )

        # 6. Dispatch to the appropriate agent
        response = self._dispatch(message, cls)

        # 7. Persist the assistant response
        MessageDAO.add(
            self.conn,
            self._session_id,
            "assistant",
            response.content,
            intent=response.intent,
            subject=response.subject,
            mode=response.mode,
        )

        return response

    def _dispatch(self, message: str, cls: Classification) -> AgentResponse:
        """Route to the correct agent based on intent classification."""
        from src.agents.subjects.base import answer_question
        from src.agents.quiz import generate_quiz
        from src.agents.interview import generate_question
        from src.agents.flashcard import generate_cards
        from src.agents.roadmap import generate_roadmap

        intent = cls.intent

        if intent == "DOUBT":
            content = answer_question(
                self.conn, self.user_id, message, cls.subject, cls.topic, cls.mode
            )
            return AgentResponse(
                content=content,
                intent=intent,
                subject=cls.subject,
                mode=cls.mode,
                topic=cls.topic,
            )

        elif intent == "QUIZ":
            result = generate_quiz(self.conn, self.user_id, cls.subject, cls.topic)
            quiz_text = _format_quiz(result)
            return AgentResponse(
                content=quiz_text,
                intent=intent,
                subject=cls.subject,
                mode=cls.mode,
                meta={"quiz": result},
            )

        elif intent == "INTERVIEW":
            # Generate next interview question
            track = cls.topic or "technical"
            result = generate_question(track, cls.subject)
            return AgentResponse(
                content=result["question"],
                intent=intent,
                subject=cls.subject,
                mode=cls.mode,
                topic=track,
                meta={"expected_points": result.get("expected_points", []),
                       "difficulty": result.get("difficulty", "medium")},
            )

        elif intent == "FLASHCARD":
            # Generate flashcards for weak topics
            cards = generate_cards(self.conn, self.user_id, cls.subject, cls.topic)
            if cards:
                card_text = "\n\n".join(
                    f"**Card {i+1}**\nQ: {c['front']}\nA: {c['back']}"
                    for i, c in enumerate(cards)
                )
                return AgentResponse(
                    content=f"Here are {len(cards)} flashcards on **{cls.topic or cls.subject or 'general'}**:\n\n{card_text}",
                    intent=intent,
                    subject=cls.subject,
                    mode=cls.mode,
                    meta={"cards": cards},
                )
            return AgentResponse(
                content="No flashcards generated. Try specifying a subject (OS/DBMS/CN/DSA) and topic.",
                intent=intent,
                subject=cls.subject,
                mode=cls.mode,
            )

        elif intent == "ROADMAP":
            result = generate_roadmap(self.conn, self.user_id)
            roadmap_text = _format_roadmap(result)
            return AgentResponse(
                content=roadmap_text,
                intent=intent,
                subject=cls.subject,
                mode=cls.mode,
                meta={"roadmap": result},
            )

        else:  # CHITCHAT or unknown
            from src.nlp.llm import generate
            r = generate(
                f"You are TechMentor, a friendly CS tutor. The student says: {message}\n\n"
                "Respond in 1-2 sentences. Be friendly and guide them to ask a CS-related question.",
                system="You are a helpful CS tutor. Keep responses short and friendly.",
                temperature=0.5,
                max_output_tokens=150,
            )
            return AgentResponse(
                content=r.text,
                intent="CHITCHAT",
                mode=cls.mode,
            )


def _intent_to_kind(intent: str) -> str:
    mapping = {
        "DOUBT": "chat",
        "QUIZ": "quiz",
        "INTERVIEW": "interview",
        "ROADMAP": "roadmap",
        "CODE": "code",
        "FLASHCARD": "flashcards",
        "CHITCHAT": "chat",
    }
    return mapping.get(intent, "chat")


def _format_quiz(quiz: dict) -> str:
    lines = ["### Quiz\n"]
    for i, q in enumerate(quiz.get("questions", []), 1):
        lines.append(f"**Q{i}.** {q['question']}")
        for ch in q.get("choices", []):
            lines.append(f"  {ch}")
        lines.append("")
    lines.append("*Select your answers and click Submit to check.*")
    return "\n".join(lines)


def _format_roadmap(result: dict) -> str:
    lines = [f"### Study Roadmap\n{result.get('summary', '')}\n"]
    for week in result.get("weeks", []):
        lines.append(f"#### Week {week['week']}")
        for item in week.get("items", []):
            lines.append(f"- **{item['subject']}/{item['topic']}** (priority {item['priority']}, ~{item.get('estimated_hours', '?')}h)")
            if item.get("rationale"):
                lines.append(f"  _{item['rationale']}_")
        lines.append("")
    return "\n".join(lines)
