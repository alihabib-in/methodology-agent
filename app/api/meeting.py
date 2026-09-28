"""Meeting lifecycle API (Jitsi meeting sessions + audit events)."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.core.db import session_scope
from app.meeting.schemas import MeetingCreate
from app.meeting.service import MeetingService
from app.models.orm import MeetingEvent
from app.realtime import events as rt

router = APIRouter(prefix="/api/v1/meetings", tags=["meetings"])


class EventRequest(BaseModel):
    event_type: str
    session_id: str | None = None
    payload: dict = {}


def _service(request: Request) -> MeetingService:
    return request.app.state.meeting_service


@router.post("")
def create_meeting(body: MeetingCreate, request: Request):
    result = _service(request).create_meeting(
        session_id=body.session_id,
        title=body.title,
        created_by=body.created_by,
        display_name=body.display_name,
    )
    broker = request.app.state.realtime_broker
    broker.publish(
        rt.MEETING_CREATED,
        session_id=body.session_id,
        meeting_id=result["meeting_id"],
        payload={"jitsi_room_name": result["jitsi_room_name"]},
    )
    broker.publish(
        rt.MEETING_READY,
        session_id=body.session_id,
        meeting_id=result["meeting_id"],
        payload={"jitsi_room_name": result["jitsi_room_name"]},
    )
    return result


@router.get("/{meeting_id}")
def get_meeting(meeting_id: str, request: Request):
    result = _service(request).get_meeting(meeting_id)
    if result is None:
        raise HTTPException(status_code=404, detail="meeting not found")
    return result


@router.post("/{meeting_id}/start")
def start_meeting(meeting_id: str, request: Request):
    result = _service(request).start_meeting(meeting_id)
    if result is None:
        raise HTTPException(status_code=404, detail="meeting not found")
    request.app.state.realtime_broker.publish(
        rt.MEETING_STARTED,
        session_id=result["session_id"],
        meeting_id=meeting_id,
    )
    return result


@router.post("/{meeting_id}/end")
def end_meeting(meeting_id: str, request: Request):
    result = _service(request).end_meeting(meeting_id)
    if result is None:
        raise HTTPException(status_code=404, detail="meeting not found")
    request.app.state.realtime_broker.publish(
        rt.MEETING_ENDED,
        session_id=result["session_id"],
        meeting_id=meeting_id,
    )
    return result


@router.post("/{meeting_id}/events")
def log_event(meeting_id: str, body: EventRequest, request: Request):
    with session_scope() as session:
        event = MeetingEvent(
            meeting_id=meeting_id,
            session_id=body.session_id,
            event_type=body.event_type,
            payload=body.payload,
        )
        session.add(event)
        session.flush()
        event_id = event.id

    request.app.state.realtime_broker.publish(
        body.event_type,
        session_id=body.session_id,
        meeting_id=meeting_id,
        payload=body.payload,
    )
    return {"event_id": event_id, "event_type": body.event_type}


@router.get("/{meeting_id}/events")
def list_events(meeting_id: str, request: Request):
    with session_scope() as session:
        events = (
            session.query(MeetingEvent)
            .filter(MeetingEvent.meeting_id == meeting_id)
            .order_by(MeetingEvent.created_at.asc())
            .all()
        )
        return [
            {
                "event_id": e.id,
                "event_type": e.event_type,
                "payload": e.payload,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ]
