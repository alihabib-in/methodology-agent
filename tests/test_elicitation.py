import json

from app.agent.methodology_agent import MethodologyAgent
from app.agents.elicitation import ElicitationAgent


class FakeLLM:
    def __init__(self):
        self.calls = []

    def chat(self, system_prompt, user_prompt, max_tokens=None):
        self.calls.append((system_prompt, user_prompt))
        return json.dumps(
            {
                "language": "en",
                "summary": "Methodology for graduate outcomes",
                "requirements": [],
                "definitions": [],
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
                    "question": "What is the target population?",
                    "reason": "needed",
                    "domain": "target_population",
                    "priority": 0.9,
                },
            }
        )

    def health(self):
        return {"available": True, "model": "fake"}


def test_elicitation_agent_returns_structured_output():
    agent = ElicitationAgent(MethodologyAgent(FakeLLM()))
    result = agent.run({"text": "We need a methodology for graduate outcomes", "language": None})
    assert result.status == "succeeded"
    assert result.agent_id == "methodology_requirement_elicitation_agent"
    assert "methodology_state" in result.outputs
    assert "gaps" in result.outputs
    assert "recommended_question" in result.outputs
