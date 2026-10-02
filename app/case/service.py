"""Application service for the Agentic Workflow domain (Phase A).

Thin transactional wrapper over :mod:`app.case.repository`. Later phases will
add the workflow orchestrator on top of this; the service intentionally stays
free of workflow logic for now.
"""

from __future__ import annotations

from app.case import repository
from app.core.db import session_scope
from app.models.case import (
    CaseArtifact,
    Evidence,
    MethodologyCase,
    Source,
    utcnow,
)


class CaseService:
    def create_case(self, *, title: str = "", **request_fields) -> MethodologyCase:
        with session_scope() as session:
            return repository.create_case(session, title=title, **request_fields)

    def get_case(self, case_id: str) -> MethodologyCase | None:
        with session_scope() as session:
            return repository.get_case(session, case_id)

    def list_cases(self, status: str | None = None) -> list[MethodologyCase]:
        with session_scope() as session:
            return repository.list_cases(session, status)

    def update_case(self, case: MethodologyCase) -> MethodologyCase:
        case.updated_at = utcnow()
        with session_scope() as session:
            repository.save_case(session, case)
        return case

    def add_source(
        self,
        source_type: str,
        *,
        reference: str | None = None,
        language: str = "unknown",
        metadata: dict | None = None,
        security: dict | None = None,
    ) -> Source:
        with session_scope() as session:
            return repository.create_source(
                session,
                source_type,
                reference=reference,
                language=language,
                metadata=metadata,
                security=security,
            )

    def add_evidence(
        self,
        source_id: str,
        statement: str,
        *,
        type: str = "business_requirement",
        location: str | None = None,
        language: str = "unknown",
        status: str = "unknown",
        provenance: dict | None = None,
    ) -> Evidence:
        with session_scope() as session:
            return repository.create_evidence(
                session,
                source_id,
                statement,
                type=type,
                location=location,
                language=language,
                status=status,
                provenance=provenance,
            )

    def list_evidence(self, source_id: str) -> list[Evidence]:
        with session_scope() as session:
            return repository.list_evidence_for_source(session, source_id)

    def create_artifact(
        self,
        case_id: str,
        artifact_type: str,
        *,
        agent_id: str | None = None,
        workflow_stage: str | None = None,
        payload: dict | None = None,
        input_refs: list[str] | None = None,
        evidence_refs: list[str] | None = None,
    ) -> CaseArtifact:
        with session_scope() as session:
            return repository.create_artifact(
                session,
                case_id,
                artifact_type,
                agent_id=agent_id,
                workflow_stage=workflow_stage,
                payload=payload,
                input_refs=input_refs,
                evidence_refs=evidence_refs,
            )

    def list_artifacts(self, case_id: str) -> list[CaseArtifact]:
        with session_scope() as session:
            return repository.list_artifacts_for_case(session, case_id)
