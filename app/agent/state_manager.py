from app.models.extraction import ExtractionResult, Requirement
from app.models.methodology_state import FieldState, MethodologyState

CONCEPT_TO_FIELD = {
    "objective": "objective",
    "target_population": "target_population",
    "population": "target_population",
    "statistical_unit": "statistical_unit",
    "reference_period": "reference_period",
    "reference_date": "reference_period",
    "frequency": "frequency",
    "geographic_scope": "geographic_scope",
}


class StateManager:
    """Maintains the structured methodology state.

    The LLM never mutates this state directly; it only proposes structured
    changes that are validated before being applied here.
    """

    def __init__(self, state: MethodologyState | None = None) -> None:
        self.state = state or MethodologyState()

    def reset(self) -> None:
        self.state = MethodologyState()

    def apply(self, extraction: ExtractionResult) -> MethodologyState:
        if extraction.objective:
            self._set_field("objective", extraction.objective, "proposed", 0.85)

        for req in extraction.requirements:
            self._apply_requirement(req)

        for req in extraction.indicators:
            self.state.indicators.append(req.model_dump())
        for req in extraction.frequencies:
            self._set_field("frequency", req.value, req.status, req.confidence)
        for req in extraction.reference_periods:
            self._set_field(
                "reference_period", req.value, req.status, req.confidence
            )
        for req in extraction.statistical_units:
            self._set_field(
                "statistical_unit", req.value, req.status, req.confidence
            )
        for req in extraction.populations:
            self._set_field(
                "target_population", req.value, req.status, req.confidence
            )
        for req in extraction.geographic_scopes:
            self._set_field(
                "geographic_scope", req.value, req.status, req.confidence
            )

        for definition in extraction.definitions:
            self.state.definitions.append(definition.model_dump())
        for source in extraction.data_sources:
            self.state.data_sources.append(source.model_dump())
        for constraint in extraction.constraints:
            self.state.constraints.append(constraint.model_dump())
        for decision in extraction.decisions:
            self.state.decisions.append(decision.model_dump())
        for open_question in extraction.open_questions:
            self.state.open_questions.append(open_question.model_dump())

        return self.state

    def _apply_requirement(self, req: Requirement) -> None:
        field = CONCEPT_TO_FIELD.get(req.concept)
        if field:
            self._set_field(field, req.value, req.status, req.confidence)

    def _set_field(
        self,
        field: str,
        value: str | None,
        status: str,
        confidence: float,
    ) -> None:
        current: FieldState = getattr(self.state, field)

        # A confirmed field must never be downgraded by an inference.
        if current.status == "confirmed" and status != "confirmed":
            return

        current.value = value
        current.status = status
        current.confidence = confidence
