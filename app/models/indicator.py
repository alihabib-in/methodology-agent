"""Indicator specification schema (Phase H).

Indicator cards are downstream outputs of the methodology workflow. Each
specification carries its methodology traceability via ``source_refs``.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class IndicatorSpecification(BaseModel):
    code: str = ""
    name: str = ""
    name_ar: str = ""
    definition: str = ""
    unit: str = ""
    population: str = ""
    numerator: str | None = None
    denominator: str | None = None
    frequency: str = ""
    data_sources: list[str] = Field(default_factory=list)
    classifications: list[str] = Field(default_factory=list)
    derivation_rule: str = ""
    quality_considerations: str = ""
    source_refs: list[str] = Field(default_factory=list)


class IndicatorSet(BaseModel):
    indicators: list[IndicatorSpecification] = Field(default_factory=list)
