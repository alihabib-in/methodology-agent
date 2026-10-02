"""Workflow definitions (Phase B).

Workflows are data, not code: a declarative set of stages with dependency,
condition, and approval rules. This mirrors the spec's YAML workflow_definition.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class StageDefinition(BaseModel):
    id: str
    agent: str
    depends_on: list[str] = Field(default_factory=list)
    condition: str | None = None  # boolean fact name evaluated by the engine
    approval_required: bool = False
    required_outputs: list[str] = Field(default_factory=list)


class WorkflowDefinition(BaseModel):
    name: str
    triggers: list[str] = Field(default_factory=list)
    stages: list[StageDefinition] = Field(default_factory=list)

    def stage(self, stage_id: str) -> StageDefinition | None:
        for stage in self.stages:
            if stage.id == stage_id:
                return stage
        return None
