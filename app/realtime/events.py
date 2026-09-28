"""Standardized real-time event envelope and event type constants."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

MEETING_CREATED = "meeting.created"
MEETING_READY = "meeting.ready"
MEETING_STARTED = "meeting.started"
MEETING_ENDED = "meeting.ended"

PARTICIPANT_JOINED = "participant.joined"
PARTICIPANT_LEFT = "participant.left"

TRANSCRIPT_SEGMENT = "transcript.segment"

AI_STATUS_CHANGED = "ai.status.changed"

OBJECTIVE_DETECTED = "objective.detected"
OBJECTIVE_UPDATED = "objective.updated"

METHODOLOGY_UPDATED = "methodology.updated"

GAP_DETECTED = "gap.detected"
GAP_UPDATED = "gap.updated"
GAP_RESOLVED = "gap.resolved"

QUESTION_GENERATED = "question.generated"
QUESTION_PRESENTED = "question.presented"
QUESTION_ASKED = "question.asked"

ANSWER_RECEIVED = "answer.received"
ANSWER_INTERPRETED = "answer.interpreted"

INSIGHT_CREATED = "insight.created"

CANDIDATE_SCOPE_UPDATED = "candidate_scope.updated"
CANDIDATE_SCOPE_READY = "candidate_scope.ready"

KNOWLEDGE_CANDIDATE = "knowledge.candidate"
KNOWLEDGE_APPROVED = "knowledge.approved"
KNOWLEDGE_PUBLISHED = "knowledge.published"

SYSTEM_ERROR = "system.error"

STATE_SNAPSHOT = "state.snapshot"


class EventEnvelope(BaseModel):
    event_id: str
    event_type: str
    session_id: str | None = None
    meeting_id: str | None = None
    timestamp: str
    sequence: int
    payload: dict[str, Any] = Field(default_factory=dict)


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_envelope(
    event_type: str,
    session_id: str | None = None,
    meeting_id: str | None = None,
    payload: dict[str, Any] | None = None,
    sequence: int = 0,
) -> EventEnvelope:
    return EventEnvelope(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        session_id=session_id,
        meeting_id=meeting_id,
        timestamp=utcnow_iso(),
        sequence=sequence,
        payload=payload or {},
    )
