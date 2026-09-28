"""Helpers to build authoritative snapshots for (re)connected clients."""

from __future__ import annotations

from app.core.db import session_scope
from app.knowledge import repository


def build_session_snapshot(agent, session_id: str) -> dict | None:
    with session_scope() as session:
        meeting = repository.get_meeting(session, session_id)
        if meeting is None:
            return None
        state = repository.load_meeting_state(meeting)

    gaps = agent.gap_detector.detect(state)
    questions = agent.question_generator.generate_many(state, gaps)
    return {
        "methodology_state": state.model_dump(),
        "gaps": gaps,
        "questions": [q.model_dump() for q in questions],
        "recommended_question": questions[0].model_dump() if questions else None,
    }
