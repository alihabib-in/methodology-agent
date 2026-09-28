"""Knowledge lifecycle endpoints: candidate -> approve/reject -> published + RAG.

Human-in-the-loop (spec 106): AI proposes, a human reviews and approves. Only
approved knowledge is indexed into Qdrant and becomes authoritative.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.core.db import session_scope
from app.core.logging import get_logger
from app.knowledge import rag, repository
from app.models.orm import KnowledgeItem
from app.realtime import events as rt

router = APIRouter()
logger = get_logger(__name__)


class CandidateRequest(BaseModel):
    concept: str
    statement: str
    domain: str | None = None
    source: str = "manual"
    evidence: str | None = None
    confidence: float = 0.0
    parent_id: str | None = None


class ApproveRequest(BaseModel):
    decision: str = "approve"
    validated_by: str | None = None


@router.post("/knowledge/candidate")
def create_candidate(body: CandidateRequest):
    with session_scope() as session:
        item = repository.create_knowledge(
            session,
            concept=body.concept,
            statement=body.statement,
            domain=body.domain,
            source=body.source,
            evidence=body.evidence,
            confidence=body.confidence,
            parent_id=body.parent_id,
        )
        return _dump(item)


@router.get("/knowledge")
def list_knowledge(status: str | None = None):
    with session_scope() as session:
        items = repository.list_knowledge(session, status=status)
        return [_dump(item) for item in items]


@router.delete("/knowledge/{item_id}")
def delete_knowledge_item(item_id: str, request: Request):
    with session_scope() as session:
        ids = [item_id]
        while True:
            children = (
                session.query(KnowledgeItem)
                .filter(KnowledgeItem.parent_id.in_(ids))
                .all()
            )
            new_ids = [c.id for c in children if c.id not in ids]
            if not new_ids:
                break
            ids.extend(new_ids)

        deleted = 0
        for kid in ids:
            item = session.get(KnowledgeItem, kid)
            if item is not None:
                repository.delete_knowledge(session, item)
                deleted += 1

    return {"deleted": deleted, "ids": ids}


@router.post("/knowledge/{item_id}/approve")
def approve(item_id: str, body: ApproveRequest, request: Request):
    decision = body.decision.lower()
    if decision not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="decision must be approve or reject")

    with session_scope() as session:
        item = repository.get_knowledge(session, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="knowledge item not found")
        if decision == "approve":
            repository.transition_knowledge(session, item, "approved", body.validated_by)
        else:
            repository.transition_knowledge(session, item, "rejected", body.validated_by)
        item_id_out = item.id
        concept = item.concept
        statement = item.statement
        domain = item.domain
        status = item.status
        meeting_id = item.meeting_id

    indexed = False
    if decision == "approve":
        indexed = _index_knowledge(item_id_out, concept, statement, domain)

    request.app.state.realtime_broker.publish(
        rt.KNOWLEDGE_APPROVED if decision == "approve" else rt.KNOWLEDGE_PUBLISHED,
        session_id=meeting_id,
        payload={"knowledge_id": item_id_out, "concept": concept, "status": status},
    )

    return {
        "knowledge_id": item_id_out,
        "status": status,
        "indexed": indexed,
    }


@router.get("/knowledge/search")
def search_knowledge(query: str, limit: int = 5):
    results = rag.retrieve(query, limit=limit)
    return {"query": query, "results": results}


def _index_knowledge(item_id: str, concept: str, statement: str, domain: str | None) -> bool:
    try:
        point_id = rag.index_knowledge(item_id, concept, statement, domain)
    except Exception as exc:  # noqa: BLE001 - indexing is best-effort
        logger.warning("knowledge indexing failed for %s: %s", item_id, exc)
        return False

    with session_scope() as session:
        item = repository.get_knowledge(session, item_id)
        if item is not None:
            repository.set_knowledge_qdrant_id(session, item, point_id)
    return True


def _dump(item: KnowledgeItem) -> dict:
    return {
        "knowledge_id": item.id,
        "concept": item.concept,
        "statement": item.statement,
        "domain": item.domain,
        "status": item.status,
        "source": item.source,
        "evidence": item.evidence,
        "confidence": item.confidence,
        "validated_by": item.validated_by,
        "effective_from": item.effective_from.isoformat() if item.effective_from else None,
        "parent_id": item.parent_id,
    }
