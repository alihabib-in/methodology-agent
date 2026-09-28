from contextlib import contextmanager

import jwt
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.meeting.service as meeting_service_module
from app.meeting.jitsi.adapter import JitsiAdapter
from app.meeting.service import MeetingService
from app.models.orm import Base

SECRET = "test-secret-0123456789-0123456789-0123456789"


@pytest.fixture
def meeting_service(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    @contextmanager
    def sqlite_session_scope():
        session = Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    monkeypatch.setattr(meeting_service_module, "session_scope", sqlite_session_scope)

    adapter = JitsiAdapter(
        base_url="https://meet.scad.local:8443",
        jwt_secret=SECRET,
    )
    return MeetingService(adapter=adapter)


def test_create_meeting(meeting_service):
    result = meeting_service.create_meeting(
        "M-000001", title="AI adoption", created_by="user1"
    )
    assert result["status"] == "ready"
    assert result["session_id"] == "M-000001"
    assert result["jitsi_room_name"].startswith("scad-")
    assert result["jitsi_url"].endswith(result["jitsi_room_name"])
    assert result["token"]


def test_meeting_lifecycle(meeting_service):
    created = meeting_service.create_meeting("M-000002")
    mid = created["meeting_id"]

    assert meeting_service.get_meeting(mid)["status"] == "ready"
    assert meeting_service.start_meeting(mid)["status"] == "live"
    assert meeting_service.end_meeting(mid)["status"] == "ended"

    final = meeting_service.get_meeting(mid)
    assert final["started_at"] is not None
    assert final["ended_at"] is not None


def test_get_missing_meeting_returns_none(meeting_service):
    assert meeting_service.get_meeting("does-not-exist") is None


def test_room_name_is_controlled_and_traceable():
    adapter = JitsiAdapter(base_url="https://meet.scad.local:8443", jwt_secret=SECRET)
    assert adapter.build_room_name("M-000123") == "scad-m-000123"
    assert adapter.validate_room("scad-m-000123")
    assert not adapter.validate_room("../../etc/passwd")


def test_jwt_token_claims():
    adapter = JitsiAdapter(base_url="https://meet.scad.local:8443", jwt_secret=SECRET)
    token = adapter.create_token("scad-m-000001", user_id="u1", display_name="Alice")
    claims = jwt.decode(
        token, SECRET, algorithms=["HS256"], audience="scad_methodology_meet"
    )
    assert claims["room"] == "scad-m-000001"
    assert claims["sub"] == "u1"
    assert claims["context"]["user"]["name"] == "Alice"
