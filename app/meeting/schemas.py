from pydantic import BaseModel, Field


class MeetingCreate(BaseModel):
    session_id: str = Field(..., min_length=1)
    title: str | None = None
    created_by: str | None = None
    display_name: str | None = None


class MeetingResponse(BaseModel):
    meeting_id: str
    session_id: str
    jitsi_room_name: str
    jitsi_url: str
    token: str | None = None
    meeting_title: str | None = None
    created_by: str | None = None
    status: str
    created_at: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
