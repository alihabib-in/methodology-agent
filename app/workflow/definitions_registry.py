"""Workflow definitions registry (Phase B).

The methodology-development workflow from the spec §5.6 is encoded as data.
Agents are registered separately (Phase C onward); this module only describes
the stage graph (dependencies, conditions, approvals).
"""

from __future__ import annotations

from app.workflow.definitions import StageDefinition, WorkflowDefinition


def methodology_workflow() -> WorkflowDefinition:
    return WorkflowDefinition(
        name="methodology_development",
        triggers=["methodology_request_confirmed"],
        stages=[
            StageDefinition(id="requirement_case", agent="methodology_case_agent"),
            StageDefinition(
                id="international_research",
                agent="international_research_agent",
                depends_on=["requirement_case"],
            ),
            StageDefinition(
                id="standardized_methodology",
                agent="standardized_methodology_agent",
                depends_on=["international_research"],
                approval_required=True,
            ),
            StageDefinition(
                id="scad_input_analysis",
                agent="scad_input_agent",
                condition="scad_documents_available",
                depends_on=["standardized_methodology"],
            ),
            StageDefinition(
                id="clarification",
                agent="methodology_qa_agent",
                condition="unresolved_scad_requirements",
                depends_on=["scad_input_analysis"],
            ),
            StageDefinition(
                id="indicator_development",
                agent="indicator_agent",
                condition="indicators_required",
                depends_on=["standardized_methodology", "clarification"],
            ),
            StageDefinition(
                id="scad_methodology",
                agent="scad_methodology_agent",
                depends_on=["standardized_methodology", "scad_input_analysis", "clarification"],
                approval_required=True,
            ),
            StageDefinition(
                id="compliance",
                agent="compliance_agent",
                depends_on=["scad_methodology"],
            ),
            StageDefinition(
                id="gap_assessment",
                agent="gap_assessment_agent",
                condition="gap_assessment_required",
                depends_on=["scad_methodology", "standardized_methodology"],
            ),
        ],
    )
