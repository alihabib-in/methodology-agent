import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


DEFAULT_RESPONSE = {
    "language": "ar",
    "summary": "Monthly active establishment indicator",
    "requirements": [],
    "definitions": [],
    "statistical_units": [],
    "populations": [],
    "reference_periods": [],
    "frequencies": [
        {
            "concept": "frequency",
            "value": "monthly",
            "status": "confirmed",
            "confidence": 0.95,
        }
    ],
    "geographic_scopes": [],
    "indicators": [
        {
            "concept": "indicator",
            "value": "active establishments",
            "status": "confirmed",
            "confidence": 0.95,
        }
    ],
    "dimensions": [],
    "data_sources": [
        {
            "name": "Business Register",
            "status": "confirmed",
            "confidence": 0.9,
        }
    ],
    "business_rules": [],
    "quality_rules": [],
    "constraints": [],
    "decisions": [],
    "open_questions": [{"concept": "definition", "status": "unknown"}],
    "recommended_question": {
        "question": "How should an establishment be defined as active?",
        "reason": "The definition is required to determine inclusion in the indicator.",
        "domain": "definition",
        "priority": 0.95,
    },
}


class FakeLLM:
    """LLM stand-in that requires no GPU, Docker, or internet."""

    def __init__(self, responses=None):
        if responses is None:
            responses = [DEFAULT_RESPONSE]
        if isinstance(responses, dict):
            responses = [responses]
        self._responses = responses
        self.calls = []

    def chat(self, system_prompt, user_prompt, max_tokens=None):
        self.calls.append((system_prompt, user_prompt))
        if len(self._responses) > 1:
            response = self._responses.pop(0)
        else:
            response = self._responses[0]
        if isinstance(response, str):
            return response
        return json.dumps(response)

    def health(self):
        return {"available": True, "model": "fake-model"}


@pytest.fixture
def fake_llm():
    return FakeLLM()


@pytest.fixture
def make_agent():
    from app.agent.methodology_agent import MethodologyAgent

    def _make(responses=None):
        return MethodologyAgent(FakeLLM(responses))

    return _make
