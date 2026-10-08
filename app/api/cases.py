"""Case + workflow API (Phase C).

Intake (meeting → case), case listing/retrieval, human confirmation, and
workflow advance/approve. These wire the Phase A domain layer and Phase B
workflow engine to HTTP.
"""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field

from app.agents.document_parser import parse_docx, parse_pdf
from app.agents.request_detector import detect_methodology_request
from app.case import repository as case_repo
from app.case.consolidation import build_case_proposal
from app.case.service import CaseService
from app.core.db import session_scope
from app.models.case import CaseStatus
from app.workflow import repository as workflow_repo
from app.workflow.definitions_registry import methodology_workflow
from app.workflow.states import ApprovalDecision

router = APIRouter(prefix="/cases", tags=["cases"])


class IntakeRequest(BaseModel):
    text: str
    language: str | None = None
    title: str | None = None
    force: bool = False


class ConfirmRequest(BaseModel):
    decision: str  # confirm | edit | request_more | cancel
    edits: dict = Field(default_factory=dict)
    decided_by: str | None = None
    comment: str | None = None


class AdvanceRequest(BaseModel):
    inputs: dict = Field(default_factory=dict)
    condition_context: dict[str, bool] | None = None


class ApproveStageRequest(BaseModel):
    decision: str  # approved | request_changes | rejected
    decided_by: str | None = None
    comment: str | None = None


def _evidence_from_extraction(
    session,
    source_id: str,
    outputs: dict,
    source_type: str = "meeting",
    filename: str | None = None,
) -> list[str]:
    extraction = outputs.get("extraction") or {}
    state = outputs.get("methodology_state") or {}
    language = extraction.get("language", "unknown")
    provenance = {"source_type": source_type, "language": language}
    if filename:
        provenance["filename"] = filename
    refs: list[str] = []

    def add(evidence_type: str, statement: str | None, status: str = "unknown") -> None:
        if not statement:
            return
        evidence = case_repo.create_evidence(
            session,
            source_id,
            statement,
            type=evidence_type,
            status=status,
            provenance=provenance,
        )
        refs.append(evidence.evidence_id)

    objective = state.get("objective") or {}
    add("business_requirement", objective.get("value"), objective.get("status", "unknown"))
    for req in extraction.get("requirements", []):
        add("requirement", f"{req.get('concept', '')}: {req.get('value')}".strip(": "), req.get("status", "unknown"))
    for definition in extraction.get("definitions", []):
        add("definition", definition.get("statement"), definition.get("status", "unknown"))
    for source in extraction.get("data_sources", []):
        add("data_source", source.get("name"), source.get("status", "unknown"))

    return refs


@router.post("")
def create_case(body: IntakeRequest, request: Request):
    registry = request.app.state.agent_registry
    elicitation = registry.get("methodology_requirement_elicitation_agent")
    if elicitation is None:
        raise HTTPException(status_code=500, detail="elicitation agent not registered")

    detection = detect_methodology_request(body.text, body.language)
    if not detection.is_methodology_request and not body.force:
        raise HTTPException(status_code=422, detail=detection.model_dump())

    result = elicitation.run({"text": body.text, "language": body.language})
    if result.status != "succeeded":
        raise HTTPException(status_code=502, detail=result.model_dump())

    outputs = result.outputs
    with session_scope() as session:
        source = case_repo.create_source(
            session,
            "meeting",
            reference=body.title or "meeting",
            language=outputs.get("extraction", {}).get("language", "unknown"),
        )
        evidence_refs = _evidence_from_extraction(session, source.source_id, outputs)
        proposal = build_case_proposal(outputs, evidence_refs=evidence_refs, title=body.title)
        proposal["status"] = "requirements_review"
        case = case_repo.create_case(session, title=body.title or "", **proposal)
        workflow_repo.save_stage_states(session, case.case_id, {"requirement_case": "WAITING_FOR_HUMAN"})

    return {"case": case, "detection": detection.model_dump()}


@router.post("/intake-document")
def create_case_from_document(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(None),
):
    registry = request.app.state.agent_registry
    agent = registry.get("requirement_document_analysis_agent")
    if agent is None:
        raise HTTPException(status_code=500, detail="document analysis agent not registered")

    filename = file.filename or "document.docx"
    data = file.file.read()
    parsed = parse_docx(data, filename)

    detection = detect_methodology_request(parsed.full_text, None)
    if not detection.is_methodology_request:
        raise HTTPException(status_code=422, detail=detection.model_dump())

    result = agent.run({"text": parsed.full_text, "language": None, "filename": filename})
    if result.status != "succeeded":
        raise HTTPException(status_code=502, detail=result.model_dump())

    outputs = result.outputs
    with session_scope() as session:
        source = case_repo.create_source(
            session,
            "word_document",
            reference=filename,
            language=outputs.get("extraction", {}).get("language", "unknown"),
        )
        evidence_refs = _evidence_from_extraction(
            session, source.source_id, outputs, source_type="word_document", filename=filename
        )
        proposal = build_case_proposal(outputs, evidence_refs=evidence_refs, title=title or parsed.title)
        proposal["status"] = "requirements_review"
        case = case_repo.create_case(session, title=title or parsed.title or "", **proposal)
        workflow_repo.save_stage_states(session, case.case_id, {"requirement_case": "WAITING_FOR_HUMAN"})

    return {"case": case, "detection": detection.model_dump()}


@router.post("/{case_id}/scad-documents")
def upload_scad_documents(case_id: str, request: Request, files: list[UploadFile] = File(...)):
    case_svc = CaseService()
    if case_svc.get_case(case_id) is None:
        raise HTTPException(status_code=404, detail="case not found")

    stored: list[str] = []
    with session_scope() as session:
        for file in files:
            filename = file.filename or "document"
            data = file.file.read()
            if filename.lower().endswith(".docx"):
                parsed = parse_docx(data, filename)
                source_type = "word_document"
            elif filename.lower().endswith(".pdf"):
                parsed = parse_pdf(data, filename)
                source_type = "pdf_document"
            else:
                continue
            source = case_repo.create_source(session, source_type, reference=filename)
            case_repo.create_artifact(
                session,
                case_id,
                "scad_document",
                workflow_stage="scad_input_analysis",
                payload={
                    "filename": filename,
                    "text": parsed.full_text,
                    "source_id": source.source_id,
                },
            )
            stored.append(filename)

    return {"case_id": case_id, "stored": stored}


@router.get("")
def list_cases(status: str | None = None):
    return CaseService().list_cases(status)


@router.get("/{case_id}")
def get_case(case_id: str, request: Request):
    case = CaseService().get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="case not found")
    with session_scope() as session:
        stage_states = workflow_repo.load_stage_states(session, case_id)
        audit_rows = workflow_repo.list_audit(session, case_id)
        audit = [
            {
                "event_type": a.event_type,
                "payload": a.payload,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in audit_rows
        ]
    return {
        "case": case,
        "workflow": {"stages": stage_states},
        "audit": audit,
    }


@router.post("/{case_id}/confirm")
def confirm_case(case_id: str, body: ConfirmRequest, request: Request):
    case_svc = CaseService()
    workflow_svc = request.app.state.workflow_service
    workflow = methodology_workflow()

    case = case_svc.get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="case not found")

    decision = body.decision.lower()
    if decision == "confirm":
        case = workflow_svc.approve_stage(
            workflow, case, "requirement_case", ApprovalDecision.APPROVED,
            decided_by=body.decided_by, comment=body.comment,
        )
    elif decision == "edit":
        for key, value in (body.edits or {}).items():
            if hasattr(case, key):
                setattr(case, key, value)
        case_svc.update_case(case)
    elif decision == "request_more":
        case.pending_actions = list(case.pending_actions) + ["request_more_information"]
        case_svc.update_case(case)
    elif decision == "cancel":
        case.status = CaseStatus.cancelled
        case_svc.update_case(case)
    else:
        raise HTTPException(status_code=400, detail="decision must be confirm|edit|request_more|cancel")

    return case


@router.post("/{case_id}/advance")
def advance_case(case_id: str, body: AdvanceRequest, request: Request):
    workflow_svc = request.app.state.workflow_service
    workflow = methodology_workflow()

    case = CaseService().get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="case not found")

    case, ran = workflow_svc.advance_case(
        workflow, case, inputs=body.inputs, condition_context=body.condition_context
    )
    return {"case": case, "ran": ran}


@router.post("/{case_id}/stages/{stage_id}/approve")
def approve_stage(case_id: str, stage_id: str, body: ApproveStageRequest, request: Request):
    decision_map = {
        "approved": ApprovalDecision.APPROVED,
        "request_changes": ApprovalDecision.REQUEST_CHANGES,
        "rejected": ApprovalDecision.REJECTED,
    }
    if body.decision not in decision_map:
        raise HTTPException(status_code=400, detail="decision must be approved|request_changes|rejected")

    workflow_svc = request.app.state.workflow_service
    workflow = methodology_workflow()

    case = CaseService().get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="case not found")

    case = workflow_svc.approve_stage(
        workflow, case, stage_id, decision_map[body.decision],
        decided_by=body.decided_by, comment=body.comment,
    )
    return case


@router.get("/{case_id}/stages/{stage_id}/output")
def get_stage_output(case_id: str, stage_id: str, request: Request):
    if CaseService().get_case(case_id) is None:
        raise HTTPException(status_code=404, detail="case not found")
    with session_scope() as session:
        return workflow_repo.latest_task_output(session, case_id, stage_id)


@router.post("/{case_id}/reset")
def reset_case(case_id: str):
    with session_scope() as session:
        case = case_repo.get_case(session, case_id)
        if case is None:
            raise HTTPException(status_code=404, detail="case not found")

        workflow_repo.reset_case_workflow(session, case_id)
        workflow_repo.save_stage_states(
            session, case_id, {"requirement_case": "WAITING_FOR_HUMAN"}
        )

        case.status = CaseStatus.requirements_review
        case.current_stage = "requirement_case"
        case.completed_stages = []
        case.pending_actions = ["requirement_case"]
        case_repo.save_case(session, case)

    return {"case_id": case_id, "status": "requirements_review"}
