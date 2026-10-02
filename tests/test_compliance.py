import json

from app.agents.compliance import ComplianceAgent


class FakeLLM:
    def chat(self, system_prompt, user_prompt, max_tokens=None):
        return json.dumps(
            {
                "findings": [
                    {"severity": "non_blocking", "item": "terminology", "detail": "terminology consistent"}
                ],
                "summary": "Looks good.",
            }
        )

    def health(self):
        return {"available": True, "model": "fake"}


def test_compliance_agent_blocks_on_empty_section():
    agent = ComplianceAgent(FakeLLM())
    result = agent.run(
        {
            "scad_methodology": {
                "methodology": {
                    "sections": [
                        {"number": "1", "title": "Introduction", "content": "text"},
                        {"number": "2", "title": "Statistical Information", "content": ""},
                    ],
                    "source_refs": ["IRIIP 2010"],
                }
            },
            "standardized_methodology": {"methodology": {"sections": []}},
        }
    )
    assert result.status == "succeeded"
    report = result.outputs["qa_report"]
    assert report["blocking_issues"]
    assert report["approval_recommendation"] == "not_recommended"
    assert any("section completeness" == f["item"] for f in report["checklist"])
