import json

from app.agents.methodology_qa import MethodologyQAAgent


class FakeLLM:
    def chat(self, system_prompt, user_prompt, max_tokens=None):
        return json.dumps(
            {
                "question_set": [
                    {
                        "question": "Which reference period?",
                        "reason": "needed",
                        "dimension": "reference period",
                        "priority": 0.9,
                    }
                ]
            }
        )

    def health(self):
        return {"available": True, "model": "fake"}


def test_qa_agent():
    agent = MethodologyQAAgent(FakeLLM())
    result = agent.run(
        {"objective": "Population", "scad_input_analysis": {"gaps": [], "questions": []}}
    )
    assert result.status == "succeeded"
    assert len(result.outputs["question_set"]) == 1
    assert result.outputs["question_set"][0]["priority"] == 0.9
