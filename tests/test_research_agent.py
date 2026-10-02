import json

from app.research.agent import InternationalResearchAgent


class FakeLLM:
    def chat(self, system_prompt, user_prompt, max_tokens=None):
        return json.dumps(
            {
                "source_register": [
                    {
                        "name": "IRIIP 2010",
                        "org": "UNSD",
                        "url": "https://unstats.un.org/unsd/iirip",
                        "category": "Index number theory",
                        "relevance": "core reference",
                    },
                    {
                        "name": "some blog",
                        "org": "user",
                        "url": "https://medium.com/@x/post",
                        "category": "x",
                        "relevance": "x",
                    },
                ],
                "findings": [{"concept": "index", "guidance": "use Laspeyres", "source": "IRIIP 2010"}],
                "research_report": "Report",
                "unresolved_questions": ["base year"],
            }
        )

    def health(self):
        return {"available": True, "model": "fake"}


def test_research_agent_filters_ugc():
    agent = InternationalResearchAgent(FakeLLM())
    result = agent.run({"objective": "AI infrastructure index", "domain": "prices"})
    assert result.status == "succeeded"
    sr = result.outputs["source_register"]
    assert len(sr) == 1
    assert sr[0]["name"] == "IRIIP 2010"
    assert sr[0]["credibility"] == "verified"
    assert result.outputs["research_report"] == "Report"
    assert result.outputs["unresolved_questions"] == ["base year"]
