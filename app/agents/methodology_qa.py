"""Methodology Q&A / Clarification Agent (Phase G).

Generates targeted, prioritized questions for the material uncertainty that
still requires SCAD input. Avoids re-asking information already resolved by
evidence or by the SCAD current-practice assessment.
"""

from __future__ import annotations

import json

from app.agent.extractor import chat_json
from app.llm.client import LLMClient
from app.workflow.contracts import Agent, AgentContract, AgentResult

SYSTEM_PROMPT = """You are a statistical methodology clarification agent.

Generate only the targeted questions needed to resolve material uncertainty for
developing a SCAD-specific methodology. Do not ask about information already
answered by the SCAD documents or by international practice. Prioritize by
methodological impact. Ask clear, non-leading questions.

Return valid JSON only."""

USER_TEMPLATE = """Indicator: {objective}

SCAD current-practice analysis gaps:
{gaps}

SCAD current-practice questions already raised:
{questions}

Generate a prioritized question set to resolve the remaining material
uncertainty. Return JSON with this shape:
{{
  "question_set": [
    {{"question": "...", "reason": "...", "dimension": "...", "priority": 0.9}}
  ],
  "reasoning": ["2-4 concise step-by-step thoughts"]
}}

Priority must be a number between 0 and 1. Return at most 10 questions."""


class MethodologyQAAgent(Agent):
    contract = AgentContract(
        id="methodology_qa_agent",
        version="1.0",
        purpose="Generate targeted clarification questions for unresolved SCAD requirements.",
        input_schema={"objective": "string", "scad_input_analysis": "object"},
        output_schema={"question_set": "list"},
        approval_required=False,
        can_modify_case=False,
        can_propose_case_updates=True,
    )

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, inputs: dict) -> AgentResult:
        objective = (inputs or {}).get("objective") or ""
        scad_input = (inputs or {}).get("scad_input_analysis") or {}

        if not objective:
            return AgentResult(
                agent_id=self.contract.id,
                status="failed",
                recommendations=[{"error": "missing objective in case context"}],
            )

        gaps_text = "\n".join(
            f"- {g.get('dimension', '')}: {g.get('description', '')}"
            for g in scad_input.get("gaps", [])
        )
        questions_text = "\n".join(
            f"- {q.get('question', '')}" for q in scad_input.get("questions", [])
        )

        user_prompt = USER_TEMPLATE.format(
            objective=objective,
            gaps=gaps_text or "(none)",
            questions=questions_text or "(none)",
        )

        try:
            data = chat_json(self._llm, SYSTEM_PROMPT, user_prompt, max_tokens=1500)
        except Exception as exc:  # noqa: BLE001
            return AgentResult(
                agent_id=self.contract.id,
                status="failed",
                recommendations=[{"error": f"qa output invalid: {exc}"}],
            )

        return AgentResult(
            agent_id=self.contract.id,
            outputs={
                "question_set": data.get("question_set", []) or [],
                "reasoning": data.get("reasoning", []) or [],
            },
            status="succeeded",
        )
