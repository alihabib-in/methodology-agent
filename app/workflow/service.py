"""Workflow service (Phase B): binds the pure engine to persistence + events.

The service is the integration layer between:
- the in-memory :class:`WorkflowEngine` (pure logic), and
- Postgres (stage states, tasks, approvals, audit log) + the real-time broker.

Agents run via the engine; the service records every transition for audit.
"""

from __future__ import annotations

from typing import Any

from app.case import repository as case_repo
from app.core.db import session_scope
from app.models.case import CaseStatus, MethodologyCase
from app.workflow import repository as workflow_repo
from app.workflow.conditions import merge_conditions
from app.workflow.contracts import AgentResult
from app.workflow.definitions import WorkflowDefinition
from app.workflow.engine import WorkflowEngine
from app.workflow.executor import Executor, InProcessExecutor
from app.workflow.registry import AgentRegistry
from app.workflow.states import ApprovalDecision, StageStatus, TaskStatus


class WorkflowService:
    def __init__(
        self,
        registry: AgentRegistry,
        executor: Executor | None = None,
        broker=None,
    ) -> None:
        self.registry = registry
        self.executor = executor or InProcessExecutor()
        self.broker = broker

    # -- engine construction -------------------------------------------------

    def _build_engine(self, workflow: WorkflowDefinition, stage_states: dict[str, str]) -> WorkflowEngine:
        engine = WorkflowEngine(workflow, self.registry, executor=self.executor)
        for stage_id, status in stage_states.items():
            if stage_id in engine.stage_states:
                engine.stage_states[stage_id] = StageStatus(status)
        return engine

    def _restore_stage_outputs(
        self,
        session,
        workflow: WorkflowDefinition,
        case_id: str,
        engine: WorkflowEngine,
    ) -> None:
        """Rehydrate prior stage outputs into the engine's in-memory cache.

        The engine is rebuilt on every ``advance`` call with only stage *states*
        restored, so a stage that runs after an approval gate would otherwise
        receive empty inputs from its upstream dependencies. Pull the last
        successful task output from persistence for every completed stage so
        dependency injection works across ``advance`` boundaries.
        """
        for stage in workflow.stages:
            if engine.stage_states.get(stage.id) != StageStatus.COMPLETED:
                continue
            outputs = workflow_repo.latest_task_output(session, case_id, stage.id)
            if outputs:
                engine.stage_outputs[stage.id] = AgentResult(
                    agent_id=stage.agent,
                    outputs=outputs,
                    status="succeeded",
                )

    def _on_event(self, session, case_id: str):
        def handler(event_type: str, payload: dict) -> None:
            workflow_repo.create_audit(session, case_id, event_type, payload)
            if self.broker:
                self.broker.publish(event_type, session_id=case_id, payload=payload)

        return handler

    def _scad_documents(self, session, case_id: str):
        artifacts = case_repo.list_artifacts_for_case(session, case_id)
        return [a for a in artifacts if a.artifact_type == "scad_document"]

    def _base_context(self, session, case_id: str) -> dict[str, bool]:
        scad_input = workflow_repo.latest_task_output(session, case_id, "scad_input_analysis")
        return {
            "scad_documents_available": bool(self._scad_documents(session, case_id)),
            "unresolved_scad_requirements": bool(
                scad_input.get("gaps") or scad_input.get("questions")
            ),
            # POC default: methodology development produces indicators.
            "indicators_required": True,
            # POC default: gap assessment requested.
            "gap_assessment_required": True,
        }

    # -- case summary --------------------------------------------------------

    def _sync_case_summary(
        self,
        case: MethodologyCase,
        workflow: WorkflowDefinition,
        engine: WorkflowEngine,
        context: dict[str, bool],
    ) -> None:
        completed = [
            sid for sid, st in engine.stage_states.items() if st == StageStatus.COMPLETED
        ]
        waiting = [
            sid for sid, st in engine.stage_states.items() if st == StageStatus.WAITING_FOR_HUMAN
        ]
        case.completed_stages = completed
        case.pending_actions = waiting

        current = None
        for stage in workflow.stages:
            if not engine.is_stage_done(stage.id, context):
                current = stage.id
                break
        case.current_stage = current

        if engine.is_complete(context):
            case.status = CaseStatus.completed
        elif "requirement_case" in waiting:
            case.status = CaseStatus.requirements_review
        else:
            case.status = CaseStatus.in_progress

    # -- operations ----------------------------------------------------------

    def advance_case(
        self,
        workflow: WorkflowDefinition,
        case: MethodologyCase,
        inputs: dict[str, Any] | None = None,
        condition_context: dict[str, bool] | None = None,
    ) -> tuple[MethodologyCase, list[dict[str, Any]]]:
        inputs = dict(inputs or {})
        # Make the case's problem statement available to every agent so they are
        # contextually aware of what they are researching / producing.
        inputs.setdefault("objective", case.objective or "")
        inputs.setdefault("domain", case.domain or "")
        inputs.setdefault("topic", case.topic or "")
        inputs.setdefault("title", case.title or "")
        inputs.setdefault("explicit_requirements", case.explicit_requirements or [])
        inputs.setdefault("constraints", case.constraints or [])
        with session_scope() as session:
            scad_documents = self._scad_documents(session, case.case_id)
            context = merge_conditions(self._base_context(session, case.case_id), condition_context)

            if scad_documents and "scad_documents" not in inputs:
                inputs["scad_documents"] = [
                    artifact.payload.get("text", "") for artifact in scad_documents
                ]

            stage_states = workflow_repo.load_stage_states(session, case.case_id)
            engine = self._build_engine(workflow, stage_states)
            self._restore_stage_outputs(session, workflow, case.case_id, engine)
            engine.on_event = self._on_event(session, case.case_id)

            ran = engine.advance(inputs=inputs, condition_context=context)

            for result in ran:
                stage_id = result["stage"]
                stage = workflow.stage(stage_id)
                agent_id = stage.agent if stage else None
                status = result["status"]
                if status in (StageStatus.COMPLETED, StageStatus.WAITING_FOR_HUMAN):
                    task_status = TaskStatus.SUCCEEDED.value
                    outputs = engine.stage_outputs.get(stage_id)
                    outputs_dict = outputs.outputs if outputs else {}
                    error = None
                else:
                    task_status = TaskStatus.FAILED.value
                    outputs_dict = {}
                    error = result.get("error") or (
                        "missing_outputs=" + ",".join(result.get("missing_outputs", []))
                    )
                workflow_repo.create_task(
                    session,
                    case.case_id,
                    stage_id,
                    agent_id,
                    task_status,
                    inputs=inputs or {},
                    outputs=outputs_dict,
                    error=error,
                )

            workflow_repo.save_stage_states(session, case.case_id, engine.status_snapshot())
            self._sync_case_summary(case, workflow, engine, context)
            case_repo.save_case(session, case)

        return case, ran

    def approve_stage(
        self,
        workflow: WorkflowDefinition,
        case: MethodologyCase,
        stage_id: str,
        decision: ApprovalDecision | str,
        decided_by: str | None = None,
        comment: str | None = None,
    ) -> MethodologyCase:
        decision = ApprovalDecision(decision)
        with session_scope() as session:
            context = merge_conditions(self._base_context(session, case.case_id))
            stage_states = workflow_repo.load_stage_states(session, case.case_id)
            engine = self._build_engine(workflow, stage_states)
            engine.on_event = self._on_event(session, case.case_id)

            engine.approve(stage_id, decision)

            workflow_repo.save_stage_states(session, case.case_id, engine.status_snapshot())
            workflow_repo.create_approval(
                session, case.case_id, stage_id, decision.value, decided_by, comment
            )
            self._sync_case_summary(case, workflow, engine, context)
            case_repo.save_case(session, case)

        return case
