from enum import Enum

from pydantic import BaseModel, Field


class KnowledgeStatus(str, Enum):
    captured = "captured"
    extracted = "extracted"
    normalized = "normalized"
    candidate = "candidate"
    validated = "validated"
    approved = "approved"
    published = "published"


class KnowledgeItem(BaseModel):
    knowledge_id: str | None = None
    concept: str
    statement: str | None = None
    status: KnowledgeStatus = KnowledgeStatus.candidate
    source: str = "meeting"
    evidence: str | None = None
    validated_by: str | None = None
    effective_from: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


# Knowledge precedence (highest wins). Used to resolve conflicts without
# silently overwriting authoritative knowledge.
KNOWLEDGE_PRECEDENCE: list[str] = [
    "approved methodology",
    "approved organizational standard",
    "validated business requirement",
    "meeting-derived knowledge",
    "ai inference",
    "ai hypothesis",
]


def precedence_rank(status_or_kind: str) -> int:
    normalized = status_or_kind.strip().lower()
    for index, label in enumerate(KNOWLEDGE_PRECEDENCE):
        if label == normalized:
            return index
    return len(KNOWLEDGE_PRECEDENCE)
