import json

from app.agents.scad_input import SCADInputAgent


class FakeLLM:
    def chat(self, system_prompt, user_prompt, max_tokens=None):
        return json.dumps(
            {
                "current_practice": [
                    {"dimension": "definitions", "scad_practice": "defines usual resident", "source": "pop.docx"}
                ],
                "mapping_matrix": [
                    {"section": "1. Conceptual Framework and Definition", "scad_status": "partial", "gap": "missing formal definition"}
                ],
                "gaps": [
                    {"dimension": "reference period", "description": "not specified", "severity": "major"}
                ],
                "questions": [
                    {"question": "What reference period?", "reason": "needed", "dimension": "reference period"}
                ],
            }
        )

    def health(self):
        return {"available": True, "model": "fake"}


def test_scad_input_agent():
    agent = SCADInputAgent(FakeLLM())
    result = agent.run(
        {
            "objective": "Population",
            "standardized_methodology": {"methodology": {"sections": []}},
            "scad_documents": ["doc text"],
        }
    )
    assert result.status == "succeeded"
    assert len(result.outputs["mapping_matrix"]) == 1
    assert result.outputs["gaps"][0]["severity"] == "major"
    assert len(result.outputs["questions"]) == 1
