import pytest

from app.agent.gap_detector import GapDetector
from app.agent.question_generator import QuestionGenerator
from app.models.extraction import RecommendedQuestion
from app.models.methodology_state import FieldState, MethodologyState


def _state(**overrides):
    fields = {
        "objective": FieldState(),
        "target_population": FieldState(),
        "statistical_unit": FieldState(),
        "reference_period": FieldState(),
        "frequency": FieldState(),
        "geographic_scope": FieldState(),
    }
    fields.update(overrides)
    return MethodologyState(**fields)


def test_gap_detector_prioritizes_definition():
    detector = GapDetector()
    gaps = detector.detect(_state())
    assert gaps
    assert gaps[0]["domain"] == "definition"
    assert gaps[0]["priority"] == pytest.approx(0.96)


def test_gap_detector_respects_confirmed_fields():
    state = _state(
        frequency=FieldState(value="monthly", status="confirmed", confidence=0.95),
    )
    gaps = GapDetector().detect(state)
    domains = [g["domain"] for g in gaps]
    assert "frequency" not in domains
    assert "definition" in domains


def test_gap_detector_empty_when_all_confirmed():
    state = _state(
        objective=FieldState(value="x", status="confirmed", confidence=0.95),
        target_population=FieldState(value="x", status="confirmed", confidence=0.95),
        statistical_unit=FieldState(value="x", status="confirmed", confidence=0.95),
        reference_period=FieldState(value="x", status="confirmed", confidence=0.95),
        frequency=FieldState(value="x", status="confirmed", confidence=0.95),
        geographic_scope=FieldState(value="x", status="confirmed", confidence=0.95),
    )
    state.definitions.append(
        {"concept": "active_establishment", "status": "confirmed", "confidence": 0.95}
    )
    state.data_sources.append(
        {"name": "BR", "status": "confirmed", "confidence": 0.95}
    )
    gaps = GapDetector().detect(state)
    assert gaps == []


def test_question_generator_uses_reference_period_template():
    gaps = [
        {
            "domain": "reference_period",
            "label": "Reference period / date",
            "reason": "The reference date determines when activity is measured.",
            "priority": 0.765,
        }
    ]
    question = QuestionGenerator().generate(gaps)
    assert question.domain == "reference_period"
    assert "reference date" in question.question.lower()


def test_question_generator_no_gaps():
    question = QuestionGenerator().generate([])
    assert question.priority == 0.0


def test_question_generator_prefers_aligned_recommendation():
    gaps = [
        {
            "domain": "definition",
            "label": "Definition of active establishment",
            "reason": "...",
            "priority": 0.96,
        }
    ]
    recommended = RecommendedQuestion(
        question="What filing criterion defines an active establishment?",
        reason="...",
        domain="definition",
        priority=0.95,
    )
    question = QuestionGenerator().generate(gaps, recommended=recommended)
    assert question.question == recommended.question


def test_inferred_definition_never_confirmed():
    from app.agent.methodology_agent import MethodologyAgent
    from tests.conftest import FakeLLM

    response = {
        "language": "en",
        "summary": "Active establishment indicator",
        "requirements": [],
        "definitions": [
            {
                "concept": "active_establishment",
                "statement": "An establishment may be active based on filing activity.",
                "status": "inferred",
                "confidence": 0.74,
            }
        ],
        "statistical_units": [],
        "populations": [],
        "reference_periods": [],
        "frequencies": [],
        "geographic_scopes": [],
        "indicators": [],
        "dimensions": [],
        "data_sources": [],
        "business_rules": [],
        "quality_rules": [],
        "constraints": [],
        "decisions": [],
        "open_questions": [],
        "recommended_question": {
            "question": "Should filing activity be the formal criterion for "
            "defining an active establishment?",
            "reason": "The definition requires confirmation.",
            "domain": "definition",
            "priority": 0.9,
        },
    }
    agent = MethodologyAgent(FakeLLM(response))
    result = agent.analyze("We usually consider an establishment active if it files something.")
    state = result["methodology_state"]
    assert state["definitions"][0]["status"] == "inferred"
