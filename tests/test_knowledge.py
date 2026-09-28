from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.knowledge import repository
from app.models.methodology_state import FieldState, MethodologyState
from app.models.orm import Base


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_meeting_lifecycle_roundtrip():
    session = _make_session()
    meeting = repository.create_meeting(session)
    assert meeting.id.startswith("M-")

    state = MethodologyState(
        frequency=FieldState(value="monthly", status="confirmed", confidence=0.9),
    )
    repository.save_meeting_state(session, meeting, state)
    session.commit()

    loaded = repository.get_meeting(session, meeting.id)
    assert loaded is not None
    restored = repository.load_meeting_state(loaded)
    assert restored.frequency.value == "monthly"
    assert restored.frequency.status == "confirmed"


def test_knowledge_lifecycle_and_provenance():
    session = _make_session()
    item = repository.create_knowledge(
        session,
        concept="active_establishment",
        statement="An establishment is active if it filed activity in the reference period.",
        domain="definition",
        source="meeting",
        evidence="M-000001",
        confidence=0.9,
    )
    assert item.id.startswith("K-")
    assert item.status == "candidate"

    repository.transition_knowledge(session, item, "approved", validated_by="tester")
    session.commit()

    assert item.status == "approved"
    assert item.validated_by == "tester"
    assert item.effective_from is not None


def test_knowledge_reject_has_no_effective_date():
    session = _make_session()
    item = repository.create_knowledge(session, concept="x", statement="y")
    repository.transition_knowledge(session, item, "rejected")
    assert item.status == "rejected"
    assert item.effective_from is None


def test_list_knowledge_filters_by_status():
    session = _make_session()
    a = repository.create_knowledge(session, concept="a", statement="1")
    b = repository.create_knowledge(session, concept="b", statement="2")
    repository.transition_knowledge(session, a, "approved")
    session.commit()

    approved = repository.list_knowledge(session, status="approved")
    assert [i.id for i in approved] == [a.id]
    assert len(repository.list_knowledge(session)) == 2
