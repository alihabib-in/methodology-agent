"""Deterministic orchestration for the demo.

Mirrors the production workflow graph (``app/workflow/definitions_registry.py``):
nine stages, two of which require human approval. The workflow advances stage by
stage and pauses at approval gates; agents only produce structured outputs and
never drive transitions themselves — the orchestrator owns the state.
"""

from __future__ import annotations

from typing import Any

from agents import AGENTS

# (stage_id, agent_key, approval_required)
STAGES: list[tuple[str, str, bool]] = [
    ("requirement_case", "elicitation", False),
    ("international_research", "research", False),
    ("standardized_methodology", "standardized", True),
    ("scad_input_analysis", "scad_input", False),
    ("clarification", "clarification", False),
    ("indicator_development", "indicator", False),
    ("scad_methodology", "scad_methodology", True),
    ("compliance", "compliance", False),
    ("gap_assessment", "gap_assessment", False),
]


class DemoWorkflow:
    """Holds the demo case + stage state. Mutated in place inside Streamlit's
    ``st.session_state`` so it survives script re-runs."""

    def __init__(self, turns: list[dict], title: str = "") -> None:
        self.turns = turns
        self.title = title
        self.case: dict[str, Any] = {}
        self.stage_status: dict[str, str] = {sid: "pending" for sid, _, _ in STAGES}
        self.stage_outputs: dict[str, dict] = {}
        self.gate: str | None = None
        self.gate_note: str = ""
        self.done = False
        self._cursor = 0

    # -- introspection --------------------------------------------------------

    def stage_label(self, stage_id: str) -> str:
        for sid, agent_key, _ in STAGES:
            if sid == stage_id:
                return AGENTS[agent_key].label
        return stage_id

    def pending_stage(self) -> str | None:
        for sid, _, _ in STAGES:
            if self.stage_status[sid] == "pending":
                return sid
        return None

    def consolidated_output(self) -> dict:
        return {
            "case": self.case,
            "standardized_sections": self.stage_outputs.get("standardized_methodology", {}).get("sections", []),
            "indicators": self.stage_outputs.get("indicator_development", {}).get("indicators", []),
            "scad_sections": self.stage_outputs.get("scad_methodology", {}).get("sections", []),
            "annotations": self.stage_outputs.get("scad_methodology", {}).get("annotations", []),
            "gap_matrix": self.stage_outputs.get("gap_assessment", {}).get("matrix", []),
            "recommendations": self.stage_outputs.get("gap_assessment", {}).get("recommendations", []),
            "open_questions": self.case.get("open_questions", []),
            "decisions": self.case.get("decisions", []),
        }

    # -- driving --------------------------------------------------------------

    def _context(self) -> dict[str, Any]:
        return {
            "turns": self.turns,
            "title": self.title,
            "case": self.case,
            "outputs": self.stage_outputs,
        }

    def start(self) -> dict:
        """Run the first agent (elicitation) to create the meeting case."""
        stage_id, agent_key, _ = STAGES[0]
        self.stage_status[stage_id] = "running"
        result = AGENTS[agent_key].run(self._context())
        self.stage_outputs[stage_id] = result
        self.case = result.get("case", {})
        self.stage_status[stage_id] = "completed"
        self._cursor = 1
        return result

    def advance(self) -> None:
        """Run the next ready stage(s) until an approval gate or completion."""
        if self.gate is not None or self.done:
            return
        while self._cursor < len(STAGES):
            stage_id, agent_key, approval = STAGES[self._cursor]
            self.stage_status[stage_id] = "running"
            self.stage_outputs[stage_id] = AGENTS[agent_key].run(self._context())
            if approval:
                self.stage_status[stage_id] = "waiting"
                self.gate = stage_id
                self.gate_note = self.stage_outputs[stage_id].get(
                    "summary", "Awaiting human approval"
                )
                return
            self.stage_status[stage_id] = "completed"
            self._cursor += 1
        self.done = True

    def approve(self, decision: str) -> None:
        """Resolve the current approval gate.

        ``decision`` is one of "approve", "reject", or "modify". Rejecting stops
        the workflow; modifying records the edit and continues.
        """
        if self.gate is None:
            return
        stage_id = self.gate
        if decision == "approve":
            self.stage_status[stage_id] = "completed"
        elif decision == "modify":
            self.stage_status[stage_id] = "completed"
            self.stage_outputs[stage_id]["summary"] += " (modified by reviewer)"
        else:  # reject
            self.stage_status[stage_id] = "rejected"
            self.done = True
            self.gate = None
            return
        self.gate = None
        self._cursor += 1
        if self._cursor >= len(STAGES):
            self.done = True
