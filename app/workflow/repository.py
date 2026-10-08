"""Workflow persistence (Phase B).

Stage states are upserted (one row per case+stage); tasks, approvals, and audit
entries are append-only. The engine stays pure; this layer records its state.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.orm import (
    AgentTaskRecord,
    ApprovalRecord,
    AuditLogRecord,
    WorkflowStageRecord,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --- Stage state -------------------------------------------------------------


def load_stage_states(session: Session, case_id: str) -> dict[str, str]:
    rows = (
        session.query(WorkflowStageRecord)
        .filter(WorkflowStageRecord.case_id == case_id)
        .all()
    )
    return {r.stage_id: r.status for r in rows}


def save_stage_states(session: Session, case_id: str, snapshot: dict[str, str]) -> None:
    for stage_id, status in snapshot.items():
        row = (
            session.query(WorkflowStageRecord)
            .filter(
                WorkflowStageRecord.case_id == case_id,
                WorkflowStageRecord.stage_id == stage_id,
            )
            .first()
        )
        if row is None:
            row = WorkflowStageRecord(case_id=case_id, stage_id=stage_id, status=status)
            session.add(row)
        else:
            row.status = status
        if status in ("COMPLETED", "SKIPPED", "FAILED", "BLOCKED", "CANCELLED"):
            row.completed_at = row.completed_at or _utcnow()


# --- Tasks --------------------------------------------------------------------


def create_task(
    session: Session,
    case_id: str,
    stage_id: str,
    agent_id: str,
    status: str,
    inputs: dict | None = None,
    outputs: dict | None = None,
    error: str | None = None,
) -> AgentTaskRecord:
    row = AgentTaskRecord(
        case_id=case_id,
        stage_id=stage_id,
        agent_id=agent_id,
        status=status,
        inputs=inputs or {},
        outputs=outputs or {},
        error=error,
        completed_at=_utcnow() if status in ("SUCCEEDED", "FAILED") else None,
    )
    session.add(row)
    session.flush()
    return row


def latest_task_output(session: Session, case_id: str, stage_id: str) -> dict:
    """Return the outputs of the most recent successful task for a stage."""
    row = (
        session.query(AgentTaskRecord)
        .filter(
            AgentTaskRecord.case_id == case_id,
            AgentTaskRecord.stage_id == stage_id,
            AgentTaskRecord.status == "SUCCEEDED",
        )
        .order_by(AgentTaskRecord.id.desc())
        .first()
    )
    return row.outputs if row else {}


# --- Approvals -----------------------------------------------------------------


def create_approval(
    session: Session,
    case_id: str,
    stage_id: str,
    decision: str,
    decided_by: str | None = None,
    comment: str | None = None,
) -> ApprovalRecord:
    row = ApprovalRecord(
        case_id=case_id,
        stage_id=stage_id,
        decision=decision,
        decided_by=decided_by,
        comment=comment,
    )
    session.add(row)
    session.flush()
    return row


# --- Audit ---------------------------------------------------------------------


def create_audit(
    session: Session, case_id: str, event_type: str, payload: dict | None = None
) -> AuditLogRecord:
    row = AuditLogRecord(case_id=case_id, event_type=event_type, payload=payload or {})
    session.add(row)
    session.flush()
    return row


def list_audit(session: Session, case_id: str) -> list[AuditLogRecord]:
    return (
        session.query(AuditLogRecord)
        .filter(AuditLogRecord.case_id == case_id)
        .order_by(AuditLogRecord.id.asc())
        .all()
    )


def reset_case_workflow(session: Session, case_id: str) -> None:
    """Clear all workflow state (stages, tasks, approvals, audit) for a case."""
    for model in (WorkflowStageRecord, AgentTaskRecord, ApprovalRecord, AuditLogRecord):
        session.query(model).filter(model.case_id == case_id).delete()
