"""Persistence layer for meetings and knowledge items (PostgreSQL)."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.methodology_state import MethodologyState
from app.models.orm import KnowledgeItem, Meeting

KNOWLEDGE_LIFECYCLE = [
    "captured",
    "extracted",
    "normalized",
    "candidate",
    "validated",
    "approved",
    "published",
]


def _next_id(session: Session, model, prefix: str) -> str:
    max_num = 0
    for row in session.query(model.id).all():
        value = row[0]
        if value and value.startswith(f"{prefix}-"):
            try:
                max_num = max(max_num, int(value.rsplit("-", 1)[-1]))
            except ValueError:
                continue
    return f"{prefix}-{max_num + 1:06d}"


# --- Meetings / sessions -----------------------------------------------------


def create_meeting(session: Session, language: str | None = None) -> Meeting:
    meeting = Meeting(id=_next_id(session, Meeting, "M"), language=language)
    session.add(meeting)
    session.flush()
    return meeting


def get_meeting(session: Session, meeting_id: str) -> Meeting | None:
    return session.get(Meeting, meeting_id)


def save_meeting_state(session: Session, meeting: Meeting, state: MethodologyState) -> None:
    meeting.methodology_state = state.model_dump()
    session.add(meeting)


def load_meeting_state(meeting: Meeting) -> MethodologyState:
    return MethodologyState.model_validate(meeting.methodology_state or {})


# --- Knowledge items ---------------------------------------------------------


def create_knowledge(
    session: Session,
    *,
    concept: str,
    statement: str,
    domain: str | None = None,
    source: str = "meeting",
    evidence: str | None = None,
    confidence: float = 0.0,
    meeting_id: str | None = None,
    parent_id: str | None = None,
) -> KnowledgeItem:
    item = KnowledgeItem(
        id=_next_id(session, KnowledgeItem, "K"),
        concept=concept,
        statement=statement,
        domain=domain,
        status="candidate",
        source=source,
        evidence=evidence,
        confidence=confidence,
        meeting_id=meeting_id,
        parent_id=parent_id,
    )
    session.add(item)
    session.flush()
    return item


def get_knowledge(session: Session, item_id: str) -> KnowledgeItem | None:
    return session.get(KnowledgeItem, item_id)


def delete_knowledge(session: Session, item: KnowledgeItem) -> None:
    session.delete(item)


def list_knowledge(
    session: Session,
    status: str | None = None,
    limit: int = 100,
) -> list[KnowledgeItem]:
    stmt = select(KnowledgeItem).order_by(KnowledgeItem.created_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(KnowledgeItem.status == status)
    return list(session.scalars(stmt))


def transition_knowledge(
    session: Session,
    item: KnowledgeItem,
    new_status: str,
    validated_by: str | None = None,
) -> KnowledgeItem:
    item.status = new_status
    if validated_by:
        item.validated_by = validated_by
    if new_status in ("approved", "published") and item.effective_from is None:
        item.effective_from = datetime.now(timezone.utc)
    session.add(item)
    return item


def set_knowledge_qdrant_id(session: Session, item: KnowledgeItem, point_id: str) -> KnowledgeItem:
    item.qdrant_point_id = point_id
    session.add(item)
    return item
