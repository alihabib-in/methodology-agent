import json

from app.agents.scad_methodology import SCADMethodologyAgent


class FakeLLM:
    def chat(self, system_prompt, user_prompt, max_tokens=None):
        return json.dumps(
            {
                "sections": [
                    {"number": "1", "title": "Introduction", "content": "Background [Aligned with: IRIIP 2010]"},
                    {"number": "2", "title": "Statistical Information", "content": "Definitions [To be confirmed by SCAD]"},
                ],
                "source_refs": ["IRIIP 2010"],
                "indicator_codes": ["IND-001"],
            }
        )

    def health(self):
        return {"available": True, "model": "fake"}


def test_scad_methodology_agent():
    agent = SCADMethodologyAgent(FakeLLM())
    result = agent.run(
        {
            "objective": "Population",
            "standardized_methodology": {"methodology": {"sections": []}},
            "scad_input_analysis": {},
            "clarification": {},
            "indicator_development": {},
        }
    )
    assert result.status == "succeeded"
    m = result.outputs["methodology"]
    assert len(m["sections"]) == 7
    assert m["sections"][0]["content"].startswith("Background")
    assert "[Aligned with:" in m["sections"][0]["content"]
    assert m["indicator_codes"] == ["IND-001"]
