import json

from app.agents.indicator import IndicatorConceptualizationAgent


class FakeLLM:
    def chat(self, system_prompt, user_prompt, max_tokens=None):
        return json.dumps(
            {
                "indicators": [
                    {
                        "code": "IND-001",
                        "name": "Population Growth Rate",
                        "name_ar": "معدل النمو السكاني",
                        "definition": "Average annual rate of change in population.",
                        "unit": "Percent",
                        "population": "Usual residents",
                        "numerator": "population change",
                        "denominator": "base population",
                        "frequency": "Annual",
                        "data_sources": ["census"],
                        "classifications": ["ISIC"],
                        "derivation_rule": "growth rate formula",
                        "quality_considerations": "accuracy",
                        "source_refs": ["UN principles"],
                    }
                ],
                "traceability": [
                    {"indicator": "Population Growth Rate", "methodology_section": "1", "source_ref": "UN principles"}
                ],
            }
        )

    def health(self):
        return {"available": True, "model": "fake"}


def test_indicator_agent():
    agent = IndicatorConceptualizationAgent(FakeLLM())
    result = agent.run(
        {
            "objective": "Population",
            "standardized_methodology": {"methodology": {"sections": []}},
            "scad_input_analysis": {},
            "clarification": {},
        }
    )
    assert result.status == "succeeded"
    assert len(result.outputs["indicators"]) == 1
    assert result.outputs["indicators"][0]["name"] == "Population Growth Rate"
    assert result.outputs["indicators"][0]["code"] == "IND-001"
    assert len(result.outputs["traceability"]) == 1
