"""Case Analysis Agent.

Runs after the methodology case is confirmed and before international research.
It analyzes the case and produces an *execution brief* that prepares the
downstream agents: the statistical domain, the standards/frameworks to research,
the key concepts to define, the sector classification, and per-agent execution
notes.
"""

from __future__ import annotations

import json

from app.agent.extractor import chat_json
from app.llm.client import LLMClient
from app.workflow.contracts import Agent, AgentContract, AgentResult

SYSTEM_PROMPT = """You are a statistical methodology case analysis agent for SCAD
(Statistics Centre - Abu Dhabi).

Given a confirmed methodology case, analyze it and produce an execution brief
that prepares the downstream agents (international research, standardized
methodology, SCAD methodology, indicators). Be specific and grounded in the
case — do not substitute a different topic.

Return valid JSON only."""

USER_TEMPLATE = """Analyze this methodology case.

Title: {title}
Objective: {objective}
Domain: {domain}
Topic: {topic}
Explicit requirements: {requirements}
Constraints: {constraints}

Produce an execution brief with exactly this JSON shape:

{{
  "objective": "restated one-sentence objective",
  "domain": "statistical domain (e.g. digital economy, labour, agriculture)",
  "topic": "specific topic",
  "research_scope": [
    "the specific standards, frameworks, classifications, NSO practices or
     benchmark indices to research for this case (e.g. OECD.AI, ITU, national
     AI strategies, Singapore/UK AI adoption indices)"
  ],
  "key_concepts": ["concepts and definitions that must be established"],
  "sector_classification": ["sectors / breakdowns relevant to this case"],
  "section_priorities": ["which methodology sections matter most"],
  "agent_brief": {{
    "research": "what international research must cover",
    "standardized_methodology": "what the standardized methodology must cover",
    "scad_methodology": "what the SCAD methodology document must cover"
  }},
  "reasoning": ["2-4 concise step-by-step thoughts"]
}}

Keep every list short (3-6 items). Return valid JSON only."""


class CaseAnalysisAgent(Agent):
    contract = AgentContract(
        id="case_analysis_agent",
        version="1.0",
        purpose="Analyze the confirmed case and produce an execution brief for downstream agents.",
        input_schema={
            "objective": "string",
            "title": "string",
            "domain": "string",
            "topic": "string",
            "explicit_requirements": "list",
            "constraints": "list",
        },
        output_schema={"case_brief": "object", "reasoning": "list"},
        approval_required=False,
        can_modify_case=False,
        can_propose_case_updates=True,
    )

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, inputs: dict) -> AgentResult:
        objective = (inputs or {}).get("objective") or ""
        title = (inputs or {}).get("title") or ""
        domain = (inputs or {}).get("domain") or ""
        topic = (inputs or {}).get("topic") or ""
        requirements = (inputs or {}).get("explicit_requirements") or []
        constraints = (inputs or {}).get("constraints") or []

        if not objective and not title:
            return AgentResult(
                agent_id=self.contract.id,
                status="failed",
                recommendations=[{"error": "no objective or title in case context"}],
            )

        user_prompt = USER_TEMPLATE.format(
            title=title or objective,
            objective=objective or title,
            domain=domain or "not specified",
            topic=topic or "not specified",
            requirements="\n".join(f"- {r}" for r in requirements) or "- (none)",
            constraints="\n".join(f"- {c}" for c in constraints) or "- (none)",
        )

        try:
            data = chat_json(self._llm, SYSTEM_PROMPT, user_prompt, max_tokens=1500)
        except Exception as exc:  # noqa: BLE001
            return AgentResult(
                agent_id=self.contract.id,
                status="failed",
                recommendations=[{"error": f"case analysis output invalid: {exc}"}],
            )

        return AgentResult(
            agent_id=self.contract.id,
            outputs={
                "case_brief": data,
                "reasoning": data.get("reasoning", []) or [],
            },
            status="succeeded",
        )
