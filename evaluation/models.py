"""Pydantic models used by the evaluation harness.

Production models (``MethodologyState``, ``MethodologyQuestion``,
``ExtractionResult``) are reused directly; these models are the additional
evaluation-only structures (transcript, evidence, state history, etc.).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TranscriptSegment(BaseModel):
    segment_id: str
    speaker_id: str
    timestamp_start: str = ""
    timestamp_end: str = ""
    language: str = "unknown"  # ar | en | mixed | unknown
    text: str
    normalized_text: str = ""


class MeetingTranscript(BaseModel):
    meeting_id: str
    title: str = ""
    language_mix: list[str] = Field(default_factory=list)
    segments: list[TranscriptSegment] = Field(default_factory=list)


class Evidence(BaseModel):
    segment_id: str
    speaker_id: str
    timestamp_start: str = ""
    timestamp_end: str = ""
    original_text: str
    language: str = "unknown"


class Fact(BaseModel):
    concept: str
    value: str | None = None
    status: str = "unknown"  # confirmed|inferred|proposed|assumption|unknown|contradicted|rejected
    confidence: float = 0.0
    evidence: list[Evidence] = Field(default_factory=list)


class Gap(BaseModel):
    concept: str
    status: str = "open"
    priority: float = 0.0
    reason: str = ""


class QuestionStatus(BaseModel):
    status: str
    timestamp: str


class Question(BaseModel):
    question_id: str
    question: str
    target_gap: str
    priority: float = 0.0
    why_asked: str = ""
    status_history: list[QuestionStatus] = Field(default_factory=list)

    @property
    def current_status(self) -> str:
        return self.status_history[-1].status if self.status_history else "candidate"


class Conflict(BaseModel):
    concept: str
    existing_value: str | None
    new_value: str | None
    evidence: list[Evidence] = Field(default_factory=list)
    status: str = "unresolved"


class KnowledgeCandidate(BaseModel):
    knowledge_type: str
    concept: str
    statement: str
    status: str = "candidate"
    confidence: float = 0.0
    evidence: list[Evidence] = Field(default_factory=list)


class CandidateScope(BaseModel):
    objective: str = ""
    population: str = ""
    statistical_unit: str = ""
    reference_period: str = ""
    geographic_scope: str = ""
    indicators: list[str] = Field(default_factory=list)
    dimensions: list[str] = Field(default_factory=list)
    data_sources: list[str] = Field(default_factory=list)
    definitions: list[dict] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    readiness_score: float = 0.0
    readiness_status: str = "in_progress"


class StateVersion(BaseModel):
    version: int
    note: str
    timestamp: str
    snapshot: dict = Field(default_factory=dict)


class EvaluationState(BaseModel):
    meeting_id: str
    title: str = ""
    objective_history: list[Fact] = Field(default_factory=list)
    facts: list[Fact] = Field(default_factory=list)
    gaps: list[Gap] = Field(default_factory=list)
    questions: list[Question] = Field(default_factory=list)
    conflicts: list[Conflict] = Field(default_factory=list)
    knowledge_candidates: list[KnowledgeCandidate] = Field(default_factory=list)
    candidate_scope: CandidateScope = Field(default_factory=CandidateScope)
    history: list[StateVersion] = Field(default_factory=list)
    state_version: int = 0
