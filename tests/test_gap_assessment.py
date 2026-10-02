import json

from app.agents.gap_assessment import GapAssessmentAgent


class FakeLLM:
    def chat(self, system_prompt, user_prompt, max_tokens=None):
        return json.dumps(
            {
                "executive_summary": "Overall partial alignment.",
                "matrix": [
                    {"dimension": "classification", "international_standard": "ISIC Rev.4", "scad_practice": "ISIC Rev.4", "gap_level": "Minor", "description": "minor", "root_cause": "none"},
                    {"dimension": "data sources", "international_standard": "multiple", "scad_practice": "limited", "gap_level": "Major", "description": "big gap", "root_cause": "legacy"},
                ],
                "priority_areas": [{"priority": "High", "gap_description": "data sources", "recommended_action": "add sources", "international_standard": "ISIC"}],
                "compliance_summary": "summary",
                "recommendations": ["improve"],
                "references": ["IRIIP"],
            }
        )

    def health(self):
        return {"available": True, "model": "fake"}


def test_gap_assessment_agent():
    agent = GapAssessmentAgent(FakeLLM())
    result = agent.run(
        {
            "objective": "Population",
            "standardized_methodology": {"methodology": {"sections": []}},
            "scad_methodology": {"methodology": {"sections": []}},
        }
    )
    assert result.status == "succeeded"
    ga = result.outputs["gap_assessment"]
    assert len(ga["matrix"]) == 2
    assert [g["dimension"] for g in result.outputs["gap_register"]] == ["data sources"]
    assert result.outputs["recommendations"] == ["improve"]
