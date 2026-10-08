"""Workflow engine (Phase B): the control plane.

The engine owns workflow state and decides which stages are ready, runs their
agents through an executor, validates required outputs, and enforces approval
gates. LLMs/agents never control transitions; they only produce structured
results that the engine validates.

Conditional stages are handled by *condition-aware* dependency resolution: a
stage whose condition is false is treated as satisfied for its dependents and
as "done" for completion, but it is never permanently skipped — if its condition
later becomes true (e.g. after an upstream stage produces gaps), it still runs.
"""

from __future__ import annotations

from typing import Any, Callable

from app.workflow import events as workflow_events
from app.workflow.contracts import AgentResult
from app.workflow.definitions import WorkflowDefinition
from app.workflow.executor import Executor, InProcessExecutor
from app.workflow.registry import AgentRegistry
from app.workflow.states import ApprovalDecision, StageStatus

EventHandler = Callable[[str, dict], None]


class WorkflowEngine:
    def __init__(
        self,
        workflow: WorkflowDefinition,
        registry: AgentRegistry,
        executor: Executor | None = None,
        on_event: EventHandler | None = None,
    ) -> None:
        self.workflow = workflow
        self.registry = registry
        self.executor = executor or InProcessExecutor()
        self.on_event = on_event
        self.stage_states: dict[str, StageStatus] = {
            stage.id: StageStatus.PENDING for stage in workflow.stages
        }
        self.stage_outputs: dict[str, AgentResult] = {}
        self.approvals: dict[str, ApprovalDecision] = {}
        self._last_context: dict[str, bool] = {}

    # -- observability -------------------------------------------------------

    def _emit(self, event_type: str, payload: dict) -> None:
        if self.on_event:
            self.on_event(event_type, payload)

    def _agent_purpose(self, agent_id: str) -> str:
        contract = self.registry.contract(agent_id)
        return contract.purpose if contract else ""

    # -- readiness -----------------------------------------------------------

    def _stage_applicable(self, stage, context: dict[str, bool]) -> bool:
        return stage.condition is None or bool(context.get(stage.condition, False))

    def _dependency_satisfied(self, dependency: str, context: dict[str, bool]) -> bool:
        # A failed or skipped stage must not wedge the workflow: treat it as
        # satisfied so downstream stages can proceed (with partial context).
        if self.stage_states[dependency] in (
            StageStatus.COMPLETED,
            StageStatus.FAILED,
            StageStatus.SKIPPED,
        ):
            return True
        dep_stage = self.workflow.stage(dependency)
        if dep_stage is not None and not self._stage_applicable(dep_stage, context):
            return True  # deactivated dependency imposes no requirement
        return False

    def _dependencies_satisfied(self, stage, context: dict[str, bool]) -> bool:
        return all(self._dependency_satisfied(d, context) for d in stage.depends_on)

    def ready_stages(self, condition_context: dict[str, bool] | None = None) -> list[str]:
        context = condition_context or {}
        ready: list[str] = []
        for stage in self.workflow.stages:
            if self.stage_states[stage.id] not in (StageStatus.PENDING, StageStatus.READY):
                continue
            if not self._stage_applicable(stage, context):
                continue
            if not self._dependencies_satisfied(stage, context):
                continue
            ready.append(stage.id)
        return ready

    # -- execution -----------------------------------------------------------

    def _inputs_for_stage(self, stage, base_inputs: dict[str, Any] | None) -> dict[str, Any]:
        """Inject completed dependency outputs into a stage's inputs, keyed by
        the dependency's stage id (agents read upstream results via this key)."""
        inputs: dict[str, Any] = dict(base_inputs or {})
        for dependency in stage.depends_on:
            output = self.stage_outputs.get(dependency)
            if output is not None:
                inputs[dependency] = output.outputs
        return inputs

    def run_stage(
        self,
        stage_id: str,
        inputs: dict[str, Any] | None = None,
        condition_context: dict[str, bool] | None = None,
    ) -> dict[str, Any]:
        stage = self.workflow.stage(stage_id)
        if stage is None:
            raise KeyError(stage_id)

        if stage_id not in self.ready_stages(condition_context):
            return {"stage": stage_id, "status": self.stage_states[stage_id], "ran": False}

        agent = self.registry.get(stage.agent)
        if agent is None:
            self.stage_states[stage_id] = StageStatus.BLOCKED
            self._emit(workflow_events.STAGE_BLOCKED, {"stage": stage_id, "agent": stage.agent, "reason": "agent not registered"})
            return {"stage": stage_id, "status": StageStatus.BLOCKED, "ran": False}

        self.stage_states[stage_id] = StageStatus.RUNNING
        self._emit(workflow_events.STAGE_STARTED, {
            "stage": stage_id,
            "agent": stage.agent,
            "purpose": self._agent_purpose(stage.agent),
        })

        try:
            result = self.executor.execute(agent, self._inputs_for_stage(stage, inputs))
        except Exception as exc:  # noqa: BLE001 - surface failure, keep workflow alive
            self.stage_states[stage_id] = StageStatus.FAILED
            self._emit(workflow_events.AGENT_FAILED, {"stage": stage_id, "agent": stage.agent, "error": str(exc)})
            return {"stage": stage_id, "status": StageStatus.FAILED, "ran": True, "error": str(exc)}

        # Agents report their own success/failure via ``AgentResult.status``; do
        # not let a failed agent silently pass as COMPLETED just because its
        # stage has no required outputs.
        if getattr(result, "status", "succeeded") != "succeeded":
            error = "; ".join(
                str(r.get("error", ""))
                for r in (result.recommendations or [])
                if r.get("error")
            ) or "agent reported failure"
            self.stage_states[stage_id] = StageStatus.FAILED
            self._emit(workflow_events.AGENT_FAILED, {"stage": stage_id, "agent": stage.agent, "error": error})
            return {"stage": stage_id, "status": StageStatus.FAILED, "ran": True, "error": error}

        missing = [o for o in stage.required_outputs if o not in result.outputs]
        if missing:
            self.stage_states[stage_id] = StageStatus.FAILED
            self._emit(workflow_events.AGENT_FAILED, {"stage": stage_id, "missing_outputs": missing})
            return {"stage": stage_id, "status": StageStatus.FAILED, "ran": True, "missing_outputs": missing}

        self.stage_outputs[stage_id] = result
        if stage.approval_required:
            self.stage_states[stage_id] = StageStatus.WAITING_FOR_HUMAN
            self._emit(workflow_events.APPROVAL_REQUESTED, {
                "stage": stage_id,
                "agent": stage.agent,
                "reasoning": result.outputs.get("reasoning", []),
                "output_keys": list(result.outputs.keys()),
            })
        else:
            self.stage_states[stage_id] = StageStatus.COMPLETED
            self._emit(workflow_events.STAGE_COMPLETED, {
                "stage": stage_id,
                "agent": stage.agent,
                "reasoning": result.outputs.get("reasoning", []),
                "output_keys": list(result.outputs.keys()),
            })

        return {"stage": stage_id, "status": self.stage_states[stage_id], "ran": True}

    def approve(self, stage_id: str, decision: ApprovalDecision) -> StageStatus:
        # Idempotent: re-approving an already-completed stage (e.g. double-click
        # or a client retry racing a prior approve) is a no-op, not an error.
        if self.stage_states.get(stage_id) == StageStatus.COMPLETED:
            return StageStatus.COMPLETED
        if self.stage_states.get(stage_id) != StageStatus.WAITING_FOR_HUMAN:
            raise RuntimeError(f"stage {stage_id} is not awaiting approval")

        if decision == ApprovalDecision.APPROVED:
            self.stage_states[stage_id] = StageStatus.COMPLETED
            self.approvals[stage_id] = decision
            self._emit(workflow_events.APPROVAL_GRANTED, {"stage": stage_id})
        elif decision == ApprovalDecision.REQUEST_CHANGES:
            self.stage_states[stage_id] = StageStatus.READY
            self.approvals[stage_id] = decision
            self._emit(workflow_events.APPROVAL_REJECTED, {"stage": stage_id, "reason": "changes requested"})
        elif decision == ApprovalDecision.REJECTED:
            self.stage_states[stage_id] = StageStatus.BLOCKED
            self.approvals[stage_id] = decision
            self._emit(workflow_events.APPROVAL_REJECTED, {"stage": stage_id, "reason": "rejected"})

        return self.stage_states[stage_id]

    def advance(
        self,
        inputs: dict[str, Any] | None = None,
        condition_context: dict[str, bool] | None = None,
        max_steps: int = 100,
    ) -> list[dict[str, Any]]:
        """Run ready stages level-by-level until a gate or completion is hit."""
        context = condition_context or {}
        self._last_context = context
        ran: list[dict[str, Any]] = []
        for _ in range(max_steps):
            ready = self.ready_stages(context)
            if not ready:
                break
            progressed = False
            for stage_id in ready:
                result = self.run_stage(stage_id, inputs, context)
                if result.get("ran"):
                    ran.append(result)
                    progressed = True
            if not progressed:
                break
        if self.is_complete(context):
            self._emit(workflow_events.WORKFLOW_COMPLETED, {"workflow": self.workflow.name})
        return ran

    # -- status --------------------------------------------------------------

    def is_stage_done(self, stage_id: str, condition_context: dict[str, bool] | None = None) -> bool:
        context = condition_context or self._last_context
        if self.stage_states[stage_id] in (
            StageStatus.COMPLETED,
            StageStatus.FAILED,
            StageStatus.SKIPPED,
        ):
            return True
        stage = self.workflow.stage(stage_id)
        return stage is not None and not self._stage_applicable(stage, context)

    def is_complete(self, condition_context: dict[str, bool] | None = None) -> bool:
        context = condition_context or self._last_context
        return all(self.is_stage_done(stage.id, context) for stage in self.workflow.stages)

    def status_snapshot(self) -> dict[str, str]:
        return {stage_id: status.value for stage_id, status in self.stage_states.items()}
