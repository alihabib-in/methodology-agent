import json

from app.agents.standardized_methodology import StandardizedMethodologyAgent
from app.models.standardized_methodology import StandardizedMethodology


class FakeLLM:
    def chat(self, system_prompt, user_prompt, max_tokens=None):
        return json.dumps(
            {
                "sections": [
                    {"number": "1", "title": "Conceptual Framework and Definition", "content": "Define the indicator per international standards."},
                    {"number": "2", "title": "Scope and Coverage", "content": "Cover relevant activities."},
                ],
                "source_refs": ["IRIIP 2010"],
            }
        )

    def health(self):
        return {"available": True, "model": "fake"}


def test_agent_produces_full_12_sections():
    agent = StandardizedMethodologyAgent(FakeLLM())
    result = agent.run(
        {
            "objective": "AI infrastructure",
            "domain": "prices",
            "international_research": {"source_register": [], "findings": []},
        }
    )
    assert result.status == "succeeded"
    methodology = result.outputs["methodology"]
    assert len(methodology["sections"]) == 12
    assert methodology["sections"][0]["title"] == "Conceptual Framework and Definition"
    assert methodology["sections"][1]["content"] == "Cover relevant activities."
    assert methodology["source_refs"] == ["IRIIP 2010"]


def test_schema_defaults():
    m = StandardizedMethodology(title="T", sections=[])
    assert m.title == "T"
    assert m.subtitle == "International Best Practice Reference"
