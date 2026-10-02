import json

from app.agent.methodology_agent import MethodologyAgent
from app.agents.document_analysis import DocumentAnalysisAgent


class FakeLLM:
    def chat(self, system_prompt, user_prompt, max_tokens=None):
        return json.dumps(
            {
                "language": "en",
                "summary": "Develop a methodology for AI infrastructure.",
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


def test_document_analysis_agent_returns_output():
    agent = DocumentAnalysisAgent(MethodologyAgent(FakeLLM()))
    result = agent.run(
        {"text": "Develop a methodology for AI infrastructure", "language": None, "filename": "x.docx"}
    )
    assert result.status == "succeeded"
    assert result.agent_id == "requirement_document_analysis_agent"
    assert "methodology_state" in result.outputs
    assert "gaps" in result.outputs
