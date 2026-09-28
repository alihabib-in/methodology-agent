from typing import Literal

from pydantic import BaseModel, Field

FieldStatus = Literal[
    "unknown",
    "inferred",
    "proposed",
    "confirmed",
    "rejected",
    "conflicting",
]


class FieldState(BaseModel):
    value: str | None = None
    status: FieldStatus = "unknown"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class MethodologyState(BaseModel):
    objective: FieldState = Field(default_factory=FieldState)
    target_population: FieldState = Field(default_factory=FieldState)
    statistical_unit: FieldState = Field(default_factory=FieldState)
    reference_period: FieldState = Field(default_factory=FieldState)
    frequency: FieldState = Field(default_factory=FieldState)
    geographic_scope: FieldState = Field(default_factory=FieldState)
    budget: FieldState = Field(default_factory=FieldState)
    scope: FieldState = Field(default_factory=FieldState)

    indicators: list[dict] = Field(default_factory=list)
    dimensions: list[dict] = Field(default_factory=list)
    data_sources: list[dict] = Field(default_factory=list)
    definitions: list[dict] = Field(default_factory=list)
    business_rules: list[dict] = Field(default_factory=list)
    quality_rules: list[dict] = Field(default_factory=list)
    constraints: list[dict] = Field(default_factory=list)
    decisions: list[dict] = Field(default_factory=list)
    open_questions: list[dict] = Field(default_factory=list)
    roles: list[dict] = Field(default_factory=list)
    success_metrics: list[dict] = Field(default_factory=list)
    training_needs: list[dict] = Field(default_factory=list)

    def scalar_fields(self) -> dict[str, FieldState]:
        return {
            "objective": self.objective,
            "target_population": self.target_population,
            "statistical_unit": self.statistical_unit,
            "reference_period": self.reference_period,
            "frequency": self.frequency,
            "geographic_scope": self.geographic_scope,
        }
