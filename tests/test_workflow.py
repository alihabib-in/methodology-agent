from app.workflow.contracts import Agent, AgentContract, AgentResult
from app.workflow.definitions import StageDefinition, WorkflowDefinition
from app.workflow.engine import WorkflowEngine
from app.workflow.registry import AgentRegistry
from app.workflow.states import ApprovalDecision, StageStatus


class FakeAgent(Agent):
    def __init__(self, agent_id, outputs=None, raise_on_run=False):
        self.contract = AgentContract(id=agent_id, purpose="test")
        self._outputs = outputs or {}
        self._raise_on_run = raise_on_run
        self.calls = 0

    def run(self, inputs):
        self.calls += 1
        if self._raise_on_run:
            raise RuntimeError("boom")
        return AgentResult(agent_id=self.contract.id, outputs=self._outputs)


def make_engine(stages, agents, conditions=None):
    workflow = WorkflowDefinition(name="test", stages=[StageDefinition(**s) for s in stages])
    registry = AgentRegistry()
    for a in agents:
        registry.register(a)
    events = []
    engine = WorkflowEngine(workflow, registry, on_event=lambda t, p: events.append((t, p)))
    return engine, events


def test_dependency_order_and_completion():
    a = FakeAgent("a", outputs={"out_a": 1})
    b = FakeAgent("b", outputs={"out_b": 2})
    engine, events = make_engine(
        [
            {"id": "s1", "agent": "a", "required_outputs": ["out_a"]},
            {"id": "s2", "agent": "b", "depends_on": ["s1"], "required_outputs": ["out_b"]},
        ],
        [a, b],
    )
    ran = engine.advance()
    assert engine.is_complete()
    assert [r["stage"] for r in ran] == ["s1", "s2"]
    assert engine.stage_outputs["s2"].outputs["out_b"] == 2


def test_approval_gate_blocks_downstream():
    a = FakeAgent("a", outputs={"out_a": 1})
    b = FakeAgent("b", outputs={"out_b": 2})
    engine, _ = make_engine(
        [
            {"id": "s1", "agent": "a", "approval_required": True, "required_outputs": ["out_a"]},
            {"id": "s2", "agent": "b", "depends_on": ["s1"], "required_outputs": ["out_b"]},
        ],
        [a, b],
    )
    engine.advance()
    assert engine.stage_states["s1"] == StageStatus.WAITING_FOR_HUMAN
    assert engine.stage_states["s2"] == StageStatus.PENDING
    assert b.calls == 0

    engine.approve("s1", ApprovalDecision.APPROVED)
    engine.advance()
    assert engine.stage_states["s1"] == StageStatus.COMPLETED
    assert engine.stage_states["s2"] == StageStatus.COMPLETED


def test_missing_required_output_fails_stage():
    a = FakeAgent("a", outputs={})  # does not produce required output
    engine, _ = make_engine(
        [{"id": "s1", "agent": "a", "required_outputs": ["out_a"]}],
        [a],
    )
    engine.advance()
    assert engine.stage_states["s1"] == StageStatus.FAILED


def test_condition_false_stage_does_not_run():
    a = FakeAgent("a", outputs={"out_a": 1})
    b = FakeAgent("b", outputs={"out_b": 2})
    engine, _ = make_engine(
        [
            {"id": "s1", "agent": "a", "required_outputs": ["out_a"]},
            {"id": "s2", "agent": "b", "condition": "scad_documents_available", "depends_on": ["s1"]},
        ],
        [a, b],
    )
    engine.advance(condition_context={"scad_documents_available": False})
    assert engine.stage_states["s1"] == StageStatus.COMPLETED
    assert engine.stage_states["s2"] == StageStatus.PENDING
    assert b.calls == 0
    assert engine.is_complete({"scad_documents_available": False})


def test_conditional_stage_runs_when_condition_true():
    a = FakeAgent("a", outputs={"out_a": 1})
    b = FakeAgent("b", outputs={"out_b": 2})
    engine, _ = make_engine(
        [
            {"id": "s1", "agent": "a", "required_outputs": ["out_a"]},
            {"id": "s2", "agent": "b", "condition": "scad_documents_available", "depends_on": ["s1"]},
        ],
        [a, b],
    )
    engine.advance(condition_context={"scad_documents_available": True})
    assert engine.stage_states["s2"] == StageStatus.COMPLETED
    assert b.calls == 1


def test_downstream_stage_not_blocked_by_deactivated_dependency():
    a = FakeAgent("a", outputs={"out_a": 1})
    b = FakeAgent("b", outputs={"out_b": 2})
    c = FakeAgent("c", outputs={"out_c": 3})
    engine, _ = make_engine(
        [
            {"id": "s1", "agent": "a", "required_outputs": ["out_a"]},
            {"id": "s2", "agent": "b", "condition": "scad_documents_available", "depends_on": ["s1"]},
            {"id": "s3", "agent": "c", "depends_on": ["s1", "s2"], "required_outputs": ["out_c"]},
        ],
        [a, b, c],
    )
    engine.advance(condition_context={"scad_documents_available": False})
    assert engine.stage_states["s2"] == StageStatus.PENDING
    assert engine.stage_states["s3"] == StageStatus.COMPLETED
    assert c.calls == 1
    assert engine.is_complete({"scad_documents_available": False})


def test_deactivated_stage_runs_when_condition_later_true():
    a = FakeAgent("a", outputs={"out_a": 1})
    b = FakeAgent("b", outputs={"out_b": 2})
    engine, _ = make_engine(
        [
            {"id": "s1", "agent": "a", "required_outputs": ["out_a"]},
            {"id": "s2", "agent": "b", "condition": "scad_documents_available", "depends_on": ["s1"]},
        ],
        [a, b],
    )
    engine.advance(condition_context={"scad_documents_available": False})
    assert b.calls == 0
    engine.advance(condition_context={"scad_documents_available": True})
    assert engine.stage_states["s2"] == StageStatus.COMPLETED
    assert b.calls == 1


def test_request_changes_reopens_stage():
    a = FakeAgent("a", outputs={"out_a": 1})
    engine, _ = make_engine(
        [{"id": "s1", "agent": "a", "approval_required": True, "required_outputs": ["out_a"]}],
        [a],
    )
    engine.advance()
    engine.approve("s1", ApprovalDecision.REQUEST_CHANGES)
    assert engine.stage_states["s1"] == StageStatus.READY
    engine.advance()
    assert engine.stage_states["s1"] == StageStatus.WAITING_FOR_HUMAN
    engine.approve("s1", ApprovalDecision.APPROVED)
    assert engine.is_complete()


def test_downstream_stage_receives_upstream_outputs():
    class RecordingAgent(Agent):
        def __init__(self, agent_id, outputs):
            self.contract = AgentContract(id=agent_id, purpose="test")
            self._outputs = outputs
            self.received = None

        def run(self, inputs):
            self.received = inputs
            return AgentResult(agent_id=self.contract.id, outputs=self._outputs)

    a = RecordingAgent("a", {"x": 1})
    b = RecordingAgent("b", {"y": 2})
    workflow = WorkflowDefinition(
        name="t",
        stages=[
            StageDefinition(id="s1", agent="a", required_outputs=["x"]),
            StageDefinition(id="s2", agent="b", depends_on=["s1"], required_outputs=["y"]),
        ],
    )
    registry = AgentRegistry()
    registry.register(a)
    registry.register(b)
    engine = WorkflowEngine(workflow, registry)
    engine.advance()
    assert b.received["s1"]["x"] == 1
