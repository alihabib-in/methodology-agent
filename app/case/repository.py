"""Persistence layer for the Agentic Workflow domain (Phase A).

Source, Evidence, MethodologyCase, and CaseArtifact records are stored as a
small set of indexed columns plus a full JSON document (the same pattern used
by ``meetings.methodology_state``). The JSON document is the authoritative
serialized object; the indexed columns exist only for querying.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.case import (
    CaseArtifact,
    Evidence,
    MethodologyCase,
    Source,
)
from app.models.orm import (
    CaseArtifactRecord,
    EvidenceRecord,
    MethodologyCaseRecord,
    SourceRecord,
)


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


# --- Sources ---------------------------------------------------------------


def create_source(
    session: Session,
    source_type: str,
    *,
    reference: str | None = None,
    language: str = "unknown",
    metadata: dict | None = None,
    security: dict | None = None,
) -> Source:
    source = Source(
        source_id=_next_id(session, SourceRecord, "SRC"),
        source_type=source_type,
        reference=reference,
        language=language,
        metadata=metadata or {},
        security=security or {},
    )
    session.add(
        SourceRecord(
            id=source.source_id,
            source_type=source.source_type.value,
            data=source.model_dump(mode="json"),
        )
    )
    session.flush()
    return source


def get_source(session: Session, source_id: str) -> Source | None:
    record = session.get(SourceRecord, source_id)
    return Source.model_validate(record.data) if record else None


# --- Evidence ---------------------------------------------------------------


def create_evidence(
    session: Session,
    source_id: str,
    statement: str,
    *,
    type: str = "business_requirement",
    location: str | None = None,
    language: str = "unknown",
    status: str = "unknown",
    provenance: dict | None = None,
) -> Evidence:
    evidence = Evidence(
        evidence_id=_next_id(session, EvidenceRecord, "E"),
        source_id=source_id,
        type=type,
        statement=statement,
        location=location,
        language=language,
        status=status,
        provenance=provenance or {},
    )
    session.add(
        EvidenceRecord(
            id=evidence.evidence_id,
            source_id=evidence.source_id,
            data=evidence.model_dump(mode="json"),
        )
    )
    session.flush()
    return evidence


def get_evidence(session: Session, evidence_id: str) -> Evidence | None:
    record = session.get(EvidenceRecord, evidence_id)
    return Evidence.model_validate(record.data) if record else None


def list_evidence_for_source(session: Session, source_id: str) -> list[Evidence]:
    records = (
        session.query(EvidenceRecord)
        .filter(EvidenceRecord.source_id == source_id)
        .order_by(EvidenceRecord.created_at.asc())
        .all()
    )
    return [Evidence.model_validate(r.data) for r in records]


# --- MethodologyCase ---------------------------------------------------------


def create_case(
    session: Session,
    *,
    title: str = "",
    **request_fields,
) -> MethodologyCase:
    case = MethodologyCase(
        case_id=_next_id(session, MethodologyCaseRecord, "METH"),
        title=title,
        **request_fields,
    )
    session.add(
        MethodologyCaseRecord(
            id=case.case_id,
            title=case.title,
            status=case.status.value,
            data=case.model_dump(mode="json"),
        )
    )
    session.flush()
    return case


def save_case(session: Session, case: MethodologyCase) -> None:
    record = session.get(MethodologyCaseRecord, case.case_id)
    if record is None:
        record = MethodologyCaseRecord(id=case.case_id)
        session.add(record)
    record.title = case.title
    record.status = case.status.value
    record.data = case.model_dump(mode="json")


def get_case(session: Session, case_id: str) -> MethodologyCase | None:
    record = session.get(MethodologyCaseRecord, case_id)
    return MethodologyCase.model_validate(record.data) if record else None


def list_cases(session: Session, status: str | None = None) -> list[MethodologyCase]:
    stmt = session.query(MethodologyCaseRecord).order_by(
        MethodologyCaseRecord.created_at.desc()
    )
    if status:
        stmt = stmt.filter(MethodologyCaseRecord.status == status)
    return [MethodologyCase.model_validate(r.data) for r in stmt.all()]


# --- Artifacts ---------------------------------------------------------------


def create_artifact(
    session: Session,
    case_id: str,
    artifact_type: str,
    *,
    agent_id: str | None = None,
    workflow_stage: str | None = None,
    payload: dict | None = None,
    input_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
) -> CaseArtifact:
    artifact = CaseArtifact(
        artifact_id=_next_id(session, CaseArtifactRecord, "ART"),
        case_id=case_id,
        agent_id=agent_id,
        workflow_stage=workflow_stage,
        artifact_type=artifact_type,
        payload=payload or {},
        input_refs=input_refs or [],
        evidence_refs=evidence_refs or [],
    )
    session.add(
        CaseArtifactRecord(
            id=artifact.artifact_id,
            case_id=artifact.case_id,
            data=artifact.model_dump(mode="json"),
        )
    )
    session.flush()
    return artifact


def list_artifacts_for_case(session: Session, case_id: str) -> list[CaseArtifact]:
    records = (
        session.query(CaseArtifactRecord)
        .filter(CaseArtifactRecord.case_id == case_id)
        .order_by(CaseArtifactRecord.created_at.asc())
        .all()
    )
    return [CaseArtifact.model_validate(r.data) for r in records]
