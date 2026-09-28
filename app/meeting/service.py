"""MeetingService: manages the meeting lifecycle, decoupled from Jitsi."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.db import session_scope
from app.meeting.jitsi.adapter import JitsiAdapter
from app.models.orm import MeetingSession

MEETING_STATUSES = ("created", "ready", "live", "ended")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MeetingService:
    def __init__(self, adapter: JitsiAdapter | None = None) -> None:
        self.adapter = adapter or JitsiAdapter()

    def create_meeting(
        self,
        session_id: str,
        title: str | None = None,
        created_by: str | None = None,
        display_name: str | None = None,
    ) -> dict:
        room_name = self.adapter.build_room_name(
            session_id, suffix=uuid.uuid4().hex[:8]
        )
        url = self.adapter.build_url(room_name)
        token = self.adapter.create_token(
            room_name,
            user_id=created_by,
            display_name=display_name,
        )

        meeting_id = str(uuid.uuid4())
        with session_scope() as session:
            meeting = MeetingSession(
                id=meeting_id,
                session_id=session_id,
                jitsi_room_name=room_name,
                meeting_title=title,
                created_by=created_by,
                status="ready",
            )
            session.add(meeting)
            session.flush()

        return self._to_dict(
            meeting_id, session_id, room_name, url, title, created_by, "ready", token
        )

    def get_meeting(self, meeting_id: str) -> dict | None:
        with session_scope() as session:
            meeting = session.get(MeetingSession, meeting_id)
            if meeting is None:
                return None
            return self._from_orm(meeting)

    def start_meeting(self, meeting_id: str) -> dict | None:
        return self._transition(meeting_id, "live", start=True)

    def end_meeting(self, meeting_id: str) -> dict | None:
        return self._transition(meeting_id, "ended", end=True)

    def _transition(self, meeting_id: str, status: str, start=False, end=False) -> dict | None:
        with session_scope() as session:
            meeting = session.get(MeetingSession, meeting_id)
            if meeting is None:
                return None
            meeting.status = status
            if start:
                meeting.started_at = _utcnow()
            if end:
                meeting.ended_at = _utcnow()
            session.add(meeting)
            session.flush()
            return self._from_orm(meeting)

    def _from_orm(self, meeting: MeetingSession) -> dict:
        return self._to_dict(
            meeting.id,
            meeting.session_id,
            meeting.jitsi_room_name,
            self.adapter.build_url(meeting.jitsi_room_name),
            meeting.meeting_title,
            meeting.created_by,
            meeting.status,
            token=None,
            created_at=meeting.created_at,
            started_at=meeting.started_at,
            ended_at=meeting.ended_at,
        )

    @staticmethod
    def _to_dict(
        meeting_id, session_id, room_name, url, title, created_by, status,
        token=None, created_at=None, started_at=None, ended_at=None,
    ) -> dict:
        return {
            "meeting_id": meeting_id,
            "session_id": session_id,
            "jitsi_room_name": room_name,
            "jitsi_url": url,
            "token": token,
            "meeting_title": title,
            "created_by": created_by,
            "status": status,
            "created_at": created_at.isoformat() if created_at else None,
            "started_at": started_at.isoformat() if started_at else None,
            "ended_at": ended_at.isoformat() if ended_at else None,
        }
