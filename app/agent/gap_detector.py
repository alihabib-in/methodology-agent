from dataclasses import dataclass

from app.models.methodology_state import MethodologyState


@dataclass(frozen=True)
class Gap:
    domain: str
    label: str
    reason: str
    methodology_impact: float
    downstream_dependency: float


GAP_DEFINITIONS: list[Gap] = [
    Gap(
        domain="definition",
        label="Definition",
        reason="The definition is required to determine what is included in the indicator.",
        methodology_impact=1.0,
        downstream_dependency=0.96,
    ),
    Gap(
        domain="objective",
        label="Statistical objective",
        reason="The objective is required to scope the whole methodology.",
        methodology_impact=0.9,
        downstream_dependency=0.9,
    ),
    Gap(
        domain="statistical_unit",
        label="Statistical unit",
        reason="The statistical unit determines what is counted and affects comparability.",
        methodology_impact=0.9,
        downstream_dependency=0.9,
    ),
    Gap(
        domain="target_population",
        label="Target population",
        reason="The target population determines the coverage of the indicator.",
        methodology_impact=0.85,
        downstream_dependency=0.85,
    ),
    Gap(
        domain="reference_period",
        label="Reference period / date",
        reason="The reference date determines when activity is measured.",
        methodology_impact=0.9,
        downstream_dependency=0.85,
    ),
    Gap(
        domain="data_source",
        label="Data source",
        reason="The data source determines where the data comes from and its update frequency.",
        methodology_impact=0.8,
        downstream_dependency=0.8,
    ),
    Gap(
        domain="frequency",
        label="Frequency",
        reason="The frequency determines how often the indicator is produced.",
        methodology_impact=0.6,
        downstream_dependency=0.6,
    ),
    Gap(
        domain="geographic_scope",
        label="Geographic scope",
        reason="The geographic scope determines the coverage area.",
        methodology_impact=0.5,
        downstream_dependency=0.5,
    ),
]


class GapDetector:
    """Deterministic, LLM-free detection of missing methodology fields."""

    def detect(self, state: MethodologyState) -> list[dict]:
        gaps: list[dict] = []
        for gap in GAP_DEFINITIONS:
            status = self._status_for(state, gap.domain)
            confidence = self._confidence_for(state, gap.domain)
            if status == "confirmed":
                continue

            priority = self._priority(gap, status)
            gaps.append(
                {
                    "domain": gap.domain,
                    "label": gap.label,
                    "reason": gap.reason,
                    "priority": round(priority, 4),
                    "confidence": round(confidence, 4),
                    "status": status,
                }
            )

        gaps.sort(key=lambda g: g["priority"], reverse=True)
        return gaps

    @staticmethod
    def _priority(gap: Gap, status: str) -> float:
        # Priority is driven by confirmation status, not the LLM's extraction
        # confidence. Inference is not confirmation: an "inferred" field is
        # still an open gap (see "Inference Is Not Fact").
        uncertainty, confidence_gap = _STATUS_FACTORS.get(status, (1.0, 1.0))
        return (
            gap.methodology_impact
            * uncertainty
            * gap.downstream_dependency
            * confidence_gap
        )

    @staticmethod
    def _status_for(state: MethodologyState, domain: str) -> str:
        field = _DOMAIN_TO_FIELD.get(domain)
        if field:
            return state.scalar_fields()[field].status
        if domain == "definition" and state.definitions:
            return max(
                (d.get("status", "unknown") for d in state.definitions),
                key=_status_rank,
            )
        if domain == "data_source" and state.data_sources:
            return max(
                (d.get("status", "unknown") for d in state.data_sources),
                key=_status_rank,
            )
        return "unknown"

    @staticmethod
    def _confidence_for(state: MethodologyState, domain: str) -> float:
        field = _DOMAIN_TO_FIELD.get(domain)
        if field:
            return state.scalar_fields()[field].confidence
        if domain == "definition" and state.definitions:
            return max(
                (d.get("confidence", 0.0) for d in state.definitions),
                default=0.0,
            )
        if domain == "data_source" and state.data_sources:
            return max(
                (d.get("confidence", 0.0) for d in state.data_sources),
                default=0.0,
            )
        return 0.0


_DOMAIN_TO_FIELD = {
    "objective": "objective",
    "target_population": "target_population",
    "statistical_unit": "statistical_unit",
    "reference_period": "reference_period",
    "frequency": "frequency",
    "geographic_scope": "geographic_scope",
}

# (uncertainty, confidence_gap) per status. A field is only "resolved" once it
# is confirmed; inferred/proposed values remain open gaps.
_STATUS_FACTORS = {
    "unknown": (1.0, 1.0),
    "inferred": (1.0, 1.0),
    "proposed": (0.85, 0.85),
    "rejected": (0.9, 0.9),
    "conflicting": (1.0, 1.0),
    "confirmed": (0.0, 0.0),
}

_STATUS_ORDER = {
    "unknown": 0,
    "rejected": 1,
    "conflicting": 2,
    "inferred": 3,
    "proposed": 4,
    "confirmed": 5,
}


def _status_rank(status: str) -> int:
    return _STATUS_ORDER.get(status, 0)
