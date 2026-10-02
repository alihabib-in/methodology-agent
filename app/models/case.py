"""Core domain models for the SCAD Methodology Agentic Workflow (Phase A).

``Source``, ``Evidence``, ``MethodologyCase``, and ``CaseArtifact`` are the
source-independent business objects. The ``MethodologyCase`` is the single
authoritative business state; agents propose changes against it but never own a
separate system of record.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class SourceType(str, Enum):
    meeting = "meeting"
    word_document = "word_document"
    pdf_document = "pdf_document"
    user_input = "user_input"


class EpistemicStatus(str, Enum):
    """Epistemic status of evidence / facts. Inference is not fact."""

    unknown = "unknown"
    inferred = "inferred"
    proposed = "proposed"
    confirmed = "confirmed"
    rejected = "rejected"
    conflicting = "conflicting"


class CaseStatus(str, Enum):
    draft = "draft"
    requirements_review = "requirements_review"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class ArtifactStatus(str, Enum):
    draft = "draft"
    in_review = "in_review"
    approved = "approved"
    rejected = "rejected"


class Source(BaseModel):
    """An original input (meeting transcript, Word document, etc.)."""

    source_id: str
    source_type: SourceType
    reference: str | None = None  # file path / transcript id / document id
    metadata: dict = Field(default_factory=dict)
    language: str = "unknown"
    security: dict = Field(default_factory=dict)
    created_at: str = Field(default_factory=utcnow)


class Evidence(BaseModel):
    """Extracted, traceable information that points back to a source."""

    evidence_id: str
    source_id: str
    type: str = "business_requirement"
    statement: str
    location: str | None = None  # e.g. "Section 1, paragraph 2"
    language: str = "unknown"
    status: EpistemicStatus = EpistemicStatus.unknown
    provenance: dict = Field(default_factory=dict)
    created_at: str = Field(default_factory=utcnow)


class MethodologyCase(BaseModel):
    """The central business object representing what SCAD asked us to develop."""

    case_id: str
    title: str = ""
    status: CaseStatus = CaseStatus.draft

    # Request
    objective: str | None = None
    business_need: str | None = None
    requested_scope: str | None = None
    expected_outcome: str | None = None

    # Subject
    domain: str | None = None
    topic: str | None = None
    population_scope: str | None = None

    # Requirements
    explicit_requirements: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    known_preferences: list[str] = Field(default_factory=list)

    # Unknowns
    missing_information: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)
    conflicts: list[dict] = Field(default_factory=list)

    # References
    evidence_refs: list[str] = Field(default_factory=list)
    decisions: list[dict] = Field(default_factory=list)

    # Workflow
    current_stage: str | None = None
    completed_stages: list[str] = Field(default_factory=list)
    pending_actions: list[str] = Field(default_factory=list)

    # Artifacts
    artifact_refs: list[str] = Field(default_factory=list)

    created_at: str = Field(default_factory=utcnow)
    updated_at: str = Field(default_factory=utcnow)


class CaseArtifact(BaseModel):
    """A versioned artifact produced by an agent during a workflow stage."""

    artifact_id: str
    case_id: str
    agent_id: str | None = None
    workflow_stage: str | None = None
    artifact_type: str = "document"
    version: int = 1
    status: ArtifactStatus = ArtifactStatus.draft
    approval_status: str | None = None
    input_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    payload: dict = Field(default_factory=dict)
    created_at: str = Field(default_factory=utcnow)
