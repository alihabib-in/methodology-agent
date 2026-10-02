"""Requirement Document Analysis Agent (Phase D).

Creates a methodology case proposal from one or more Word requirement
documents. It reuses the same deterministic engine as the meeting elicitation
agent (extract → state → gaps → question) so document and meeting cases
converge to the same ``MethodologyCase`` model.
"""

from __future__ import annotations

from app.agent.methodology_agent import MethodologyAgent
from app.workflow.contracts import Agent, AgentContract, AgentResult


class DocumentAnalysisAgent(Agent):
    contract = AgentContract(
        id="requirement_document_analysis_agent",
        version="1.0",
        purpose="Create a methodology case proposal from Word requirement documents.",
        input_schema={"text": "string", "language": "string|null", "filename": "string|null"},
        output_schema={
            "summary": "string",
            "extraction": "object",
            "methodology_state": "object",
            "gaps": "list",
            "recommended_question": "object",
        },
        approval_required=False,
        can_modify_case=False,
        can_propose_case_updates=True,
    )

    def __init__(self, agent: MethodologyAgent) -> None:
        self._agent = agent

    def run(self, inputs: dict) -> AgentResult:
        text = (inputs or {}).get("text", "")
        language = (inputs or {}).get("language")
        result = self._agent.analyze(text, language)

        if result.get("parse_error"):
            return AgentResult(
                agent_id=self.contract.id,
                status="failed",
                recommendations=[{"error": result.get("error")}],
            )

        return AgentResult(
            agent_id=self.contract.id,
            outputs={
                "summary": result.get("summary"),
                "extraction": result.get("extraction"),
                "methodology_state": result.get("methodology_state"),
                "gaps": result.get("gaps"),
                "recommended_question": result.get("recommended_question"),
            },
            status="succeeded",
        )
