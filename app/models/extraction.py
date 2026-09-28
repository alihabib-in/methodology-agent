from typing import Literal

from pydantic import BaseModel, Field

EvidenceStatus = Literal[
    "observed",
    "inferred",
    "proposed",
    "confirmed",
    "rejected",
]

ItemStatus = Literal[
    "unknown",
    "inferred",
    "proposed",
    "confirmed",
    "rejected",
    "conflicting",
]


class Evidence(BaseModel):
    text: str = ""
    language: str = "auto"
    status: EvidenceStatus = "observed"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class Requirement(BaseModel):
    concept: str = ""
    value: str | None = None
    domain: str = "requirement"
    status: ItemStatus = "inferred"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: list[Evidence] = Field(default_factory=list)


class Definition(BaseModel):
    concept: str = ""
    statement: str | None = None
    status: ItemStatus = "inferred"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: list[Evidence] = Field(default_factory=list)


class DataSource(BaseModel):
    name: str = ""
    update_frequency: str | None = None
    status: ItemStatus = "inferred"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: list[Evidence] = Field(default_factory=list)


class Decision(BaseModel):
    concept: str = ""
    value: str | None = None
    status: ItemStatus = "inferred"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: list[Evidence] = Field(default_factory=list)


class Constraint(BaseModel):
    concept: str = ""
    value: str | None = None
    status: ItemStatus = "inferred"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: list[Evidence] = Field(default_factory=list)


class OpenQuestion(BaseModel):
    concept: str = ""
    status: ItemStatus = "unknown"
    note: str | None = None


class RecommendedQuestion(BaseModel):
    question: str = ""
    reason: str | None = None
    domain: str | None = None
    priority: float = Field(default=0.0, ge=0.0, le=1.0)


class ExtractionResult(BaseModel):
    language: str = "auto"
    summary: str | None = None
    requirements: list[Requirement] = Field(default_factory=list)
    definitions: list[Definition] = Field(default_factory=list)
    statistical_units: list[Requirement] = Field(default_factory=list)
    populations: list[Requirement] = Field(default_factory=list)
    reference_periods: list[Requirement] = Field(default_factory=list)
    frequencies: list[Requirement] = Field(default_factory=list)
    geographic_scopes: list[Requirement] = Field(default_factory=list)
    indicators: list[Requirement] = Field(default_factory=list)
    dimensions: list[Requirement] = Field(default_factory=list)
    data_sources: list[DataSource] = Field(default_factory=list)
    business_rules: list[Requirement] = Field(default_factory=list)
    quality_rules: list[Requirement] = Field(default_factory=list)
    constraints: list[Constraint] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
    open_questions: list[OpenQuestion] = Field(default_factory=list)
    recommended_question: RecommendedQuestion | None = None
