"""Methodology-request detection (Phase C).

Deterministic signal matching over bilingual (Arabic/English) text, per spec
§5.2/§5.3. The confidence value is advisory and never replaces human
confirmation. A future enhancement can add an LLM classifier on top of the same
``detect_methodology_request`` interface.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

STRONG_SIGNALS = [
    "develop a methodology", "develop methodology", "methodology for",
    "need a methodology", "need methodology", "new methodology",
    "standardized approach", "standardised approach", "standardize", "standardise",
    "standardized", "standardised", "how should we measure", "how to measure",
    "define the indicator", "define indicator", "statistical definition",
    "formal methodology", "standard methodology", "establish how this statistic",
    "منهجية", "تطوير منهجية", "توحيد", "منهجية إحصائية", "تطوير مؤشر",
]

WEAK_SIGNALS = [
    "indicator", "definition", "data source", "frequency", "classification",
    "statistical unit", "target population", "reference period", "coverage",
    "مؤشر", "تعريف", "المصدر", "التكرار", "التصنيف", "الوحدة الإحصائية",
    "السكان المستهدفون", "الفترة المرجعية",
]


class RequestDetection(BaseModel):
    is_methodology_request: bool
    confidence: float
    request_type: str = "new_methodology"
    reason: str = ""
    signals: list[str] = Field(default_factory=list)


def detect_methodology_request(text: str, language: str | None = None) -> RequestDetection:
    text = (text or "").lower()
    strong = [s for s in STRONG_SIGNALS if s in text]
    weak = [s for s in WEAK_SIGNALS if s in text]

    if strong:
        request_type = (
            "standardize_methodology"
            if any("standard" in s or "توحيد" in s for s in strong)
            else "new_methodology"
        )
        return RequestDetection(
            is_methodology_request=True,
            confidence=0.9,
            request_type=request_type,
            reason="Explicit request to develop/standardize a methodology.",
            signals=strong + weak,
        )

    if weak:
        return RequestDetection(
            is_methodology_request=True,
            confidence=0.6,
            request_type="new_methodology",
            reason="Discussion contains methodology topics but no explicit request.",
            signals=weak,
        )

    return RequestDetection(
        is_methodology_request=False,
        confidence=0.1,
        request_type="none",
        reason="No methodology request detected.",
        signals=[],
    )
