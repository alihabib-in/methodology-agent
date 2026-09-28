"""Adapters that expose a common ``analyze(text, language, state)`` interface.

- ``ProductionAdapter`` / ``LocalAdapter`` reuse the production
  ``MethodologyAgent`` (with the local OpenAI-compatible LLM gateway).
- ``MockAdapter`` replaces only the LLM extraction step with deterministic
  keyword rules while reusing the production ``StateManager``, ``GapDetector``
  and ``QuestionGenerator`` (which are already deterministic).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.agent.gap_detector import GapDetector
from app.agent.methodology_agent import MethodologyAgent
from app.agent.question_generator import QuestionGenerator
from app.agent.state_manager import StateManager
from app.llm.client import LLMClient
from app.models.extraction import (
    DataSource,
    Definition,
    ExtractionResult,
    Requirement,
)

AnalyzeResult = dict


class Adapter(ABC):
    @abstractmethod
    def analyze(self, text: str, language: str, state) -> AnalyzeResult:
        """Return the same shape as ``MethodologyAgent.analyze``."""


class ProductionAdapter(Adapter):
    """Reuse the production MethodologyAgent against the local LLM gateway."""

    def __init__(self, base_url: str, model: str, timeout: float, temperature: float, use_rag: bool) -> None:
        llm = LLMClient(base_url=base_url, model=model, timeout=timeout, temperature=temperature)
        self.agent = MethodologyAgent(llm)
        self.use_rag = use_rag

    def analyze(self, text: str, language: str, state) -> AnalyzeResult:
        return self.agent.analyze(text, language, state=state, use_rag=self.use_rag)


class MockAdapter(Adapter):
    """Deterministic, LLM-free extraction for testing pipeline mechanics.

    Only the extraction is mocked; state application, gap detection and question
    generation still use the real production logic.
    """

    def __init__(self) -> None:
        self.gap_detector = GapDetector()
        self.question_generator = QuestionGenerator()

    def analyze(self, text: str, language: str, state) -> AnalyzeResult:
        extraction = self._extract(text, language)
        updated = StateManager(state).apply(extraction)
        gaps = self.gap_detector.detect(updated)
        question = self.question_generator.generate(gaps, recommended=extraction.recommended_question)
        return {
            "summary": extraction.summary,
            "extraction": extraction.model_dump(),
            "methodology_state": updated.model_dump(),
            "gaps": gaps,
            "recommended_question": question.model_dump(),
            "relevant_knowledge": [],
            "parse_error": False,
        }

    @staticmethod
    def _extract(text: str, language: str) -> ExtractionResult:
        t = text.lower()

        requirements = []
        if any(k in t for k in ("indicator", "مؤشر", " index", "measure", "قياس", "inflation", "price index")):
            requirements.append(
                Requirement(concept="objective", value="Compile a statistical indicator / price index",
                            status="proposed", confidence=0.65)
            )

        frequencies = []
        if any(k in t for k in ("quarterly", "ربع سنوي")):
            frequencies.append(Requirement(concept="frequency", value="quarterly", status="confirmed", confidence=0.9))
        elif any(k in t for k in ("monthly", "شهري")):
            frequencies.append(Requirement(concept="frequency", value="monthly", status="confirmed", confidence=0.9))
        elif any(k in t for k in ("annual", "yearly", "سنوي")):
            frequencies.append(Requirement(concept="frequency", value="annual", status="confirmed", confidence=0.9))
        elif any(k in t for k in ("weekly", "أسبوعي")):
            frequencies.append(Requirement(concept="frequency", value="weekly", status="confirmed", confidence=0.85))

        reference_periods = []
        if any(k in t for k in ("december", "previous year", "reference period", "فترة مرجعية")):
            reference_periods.append(Requirement(concept="reference_period", value="December of the previous year",
                                                status="proposed", confidence=0.7))
        elif any(k in t for k in ("2025", "2026")):
            reference_periods.append(Requirement(concept="reference_period", value="2025", status="proposed", confidence=0.7))

        statistical_units = []
        if any(k in t for k in ("establishment", "منشأة", "منشآت")):
            statistical_units.append(Requirement(concept="statistical_unit", value="establishment",
                                                 status="confirmed", confidence=0.85))
        elif any(k in t for k in ("product", " item", "transaction", "منتج", "سلعة")):
            statistical_units.append(Requirement(concept="statistical_unit", value="product",
                                                 status="proposed", confidence=0.7))

        populations = []
        if any(k in t for k in ("establishment", "منشأة", "منشآت")):
            populations.append(Requirement(concept="target_population", value="establishments",
                                           status="proposed", confidence=0.7))
        elif any(k in t for k in ("consumer", "household", "مستهلك", "basket")):
            populations.append(Requirement(concept="target_population", value="consumer goods / households",
                                           status="proposed", confidence=0.6))

        geographic_scopes = []
        if any(k in t for k in ("euro area", "european", "member state", "europe")):
            geographic_scopes.append(Requirement(concept="geographic_scope", value="euro area / European Union",
                                                 status="confirmed", confidence=0.9))
        elif any(k in t for k in ("abu dhabi", "أبوظبي", "emirate", "إمارة")):
            geographic_scopes.append(Requirement(concept="geographic_scope", value="Abu Dhabi",
                                                 status="confirmed", confidence=0.9))

        definitions = []
        if any(k in t for k in ("consumer price index", "inflation", "hicp", "price index")):
            definitions.append(Definition(concept="consumer_price_index",
                                          statement="A measure of the change in the price of a basket of consumer goods and services over time",
                                          status="confirmed", confidence=0.85))
        elif "active" in t and ("establishment" in t or "منشأة" in text):
            definitions.append(Definition(concept="active_establishment",
                                          statement="An establishment with economic activity during the reference period",
                                          status="proposed", confidence=0.7))

        data_sources = []
        if any(k in t for k in ("scanner", "web scrap", "big data")):
            data_sources.append(DataSource(name="scanner / web-scraped data", status="confirmed", confidence=0.8))
        elif any(k in t for k in ("register", "سجل", "survey", "مسح")):
            data_sources.append(DataSource(name="business register", status="proposed", confidence=0.6))

        indicators = []
        if any(k in t for k in ("indicator", "مؤشر", " index", "inflation")):
            indicators.append(Requirement(concept="indicator", value="price index / inflation rate",
                                          status="proposed", confidence=0.7))

        return ExtractionResult(
            language=language,
            summary="Discussion about compiling a statistical indicator.",
            requirements=requirements,
            frequencies=frequencies,
            reference_periods=reference_periods,
            statistical_units=statistical_units,
            populations=populations,
            geographic_scopes=geographic_scopes,
            definitions=definitions,
            data_sources=data_sources,
            indicators=indicators,
        )


def build_adapter(config) -> Adapter:
    if config.mode == "mock":
        return MockAdapter()
    # production and local both use the real pipeline + local gateway.
    return ProductionAdapter(
        base_url=config.llm_base_url,
        model=config.llm_model,
        timeout=config.llm_timeout,
        temperature=config.llm_temperature,
        use_rag=config.use_rag,
    )
