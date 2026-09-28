"""Normalized meeting event types (decoupled from raw Jitsi events)."""

MEETING_CREATED = "meeting.created"
MEETING_READY = "meeting.ready"
MEETING_STARTED = "meeting.started"
PARTICIPANT_JOINED = "participant.joined"
PARTICIPANT_LEFT = "participant.left"
MEETING_LEFT = "meeting.left"
MEETING_ENDED = "meeting.ended"

LIFECYCLE = [MEETING_CREATED, MEETING_READY, MEETING_STARTED, MEETING_ENDED]
