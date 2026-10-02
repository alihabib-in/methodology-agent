"""Gap assessment schema (Phase J)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GapItem(BaseModel):
    dimension: str = ""
    international_standard: str = ""
    scad_practice: str = ""
    gap_level: str = ""  # None | Minor | Moderate | Major
    description: str = ""
    root_cause: str = ""


class GapAssessment(BaseModel):
    executive_summary: str = ""
    matrix: list[GapItem] = Field(default_factory=list)
    priority_areas: list[dict] = Field(default_factory=list)
    compliance_summary: str = ""
    recommendations: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
