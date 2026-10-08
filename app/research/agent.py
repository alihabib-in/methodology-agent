"""International Research Agent (Phase E).

Identifies the authoritative international standards, frameworks,
classifications, and NSO best practices relevant to a methodology request. The
LLM produces a candidate source register; the credibility policy then discards
user-generated content and annotates the rest.
"""

from __future__ import annotations

import json

from app.agent.extractor import chat_json
from app.llm.client import LLMClient
from app.research.sources import RESEARCH_CATEGORIES, STANDARDS_REFERENCE, filter_source_register
from app.workflow.contracts import Agent, AgentContract, AgentResult

RESEARCH_SYSTEM_PROMPT = """You are a statistical methodology research agent.

Identify the authoritative international standards, frameworks, classifications,
and NSO best practices relevant to a statistical indicator.

Rely ONLY on verified published information from credible statistical
organizations: UN / UNSD / UNECE, ILO, OECD, IMF, World Bank, Eurostat, SDMX,
GCC-Stat, and national statistical offices. Never cite blogs, videos, forums,
wikis, or any user-generated content. If you are unsure of a URL, omit it
rather than invent one.

Return valid JSON only."""

RESEARCH_USER_TEMPLATE = """Research the international methodology for this indicator.

Objective / topic: {objective}
Domain: {domain}

Case-specific research scope (target these):
{research_scope}

Organize sources by these categories:
{categories}

Use these authoritative standards as the primary frame of reference:
{standards}

Return JSON with this shape:
{{
  "source_register": [
    {{"name": "manual/handbook/classification", "org": "issuing organization",
      "url": "official URL or empty string", "category": "category name",
      "relevance": "one-sentence relevance"}}
  ],
  "findings": [
    {{"concept": "methodological concept", "guidance": "what international practice says",
      "source": "name of the source"}}
  ],
  "research_report": "a concise synthesis paragraph",
  "unresolved_questions": ["question that needs SCAD clarification"],
  "reasoning": ["2-4 concise step-by-step thoughts"]
}}

Provide at most 12 sources with one-sentence relevance. Keep the whole response
compact so it fits in the output limit. Return valid JSON only."""


class InternationalResearchAgent(Agent):
    contract = AgentContract(
        id="international_research_agent",
        version="1.0",
        purpose="Identify relevant international standards and NSO best practices for a methodology.",
        input_schema={"objective": "string", "topic": "string", "domain": "string"},
        output_schema={
            "source_register": "list",
            "findings": "list",
            "research_report": "string",
            "unresolved_questions": "list",
        },
        approval_required=False,
        can_modify_case=False,
        can_propose_case_updates=True,
    )

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, inputs: dict) -> AgentResult:
        objective = (inputs or {}).get("objective") or (inputs or {}).get("topic") or ""
        domain = (inputs or {}).get("domain") or ""
        brief = ((inputs or {}).get("case_analysis") or {}).get("case_brief") or {}
        research_scope = brief.get("research_scope") or []

        if not objective:
            return AgentResult(
                agent_id=self.contract.id,
                status="failed",
                recommendations=[{"error": "missing objective in case context"}],
            )

        user_prompt = RESEARCH_USER_TEMPLATE.format(
            objective=objective,
            domain=domain or "not specified",
            categories="\n".join(f"- {c}" for c in RESEARCH_CATEGORIES),
            standards="\n".join(
                f"- {s['standard']} ({s['org']}): {s['purpose']}" for s in STANDARDS_REFERENCE
            ),
            research_scope="\n".join(f"- {s}" for s in research_scope) or "- (none)",
        )

        try:
            data = chat_json(self._llm, RESEARCH_SYSTEM_PROMPT, user_prompt, max_tokens=2500)
        except Exception as exc:  # noqa: BLE001
            return AgentResult(
                agent_id=self.contract.id,
                status="failed",
                recommendations=[{"error": f"research output invalid: {exc}"}],
            )

        source_register = filter_source_register(data.get("source_register", []) or [])

        return AgentResult(
            agent_id=self.contract.id,
            outputs={
                "source_register": source_register,
                "findings": data.get("findings", []) or [],
                "research_report": data.get("research_report", "") or "",
                "unresolved_questions": data.get("unresolved_questions", []) or [],
                "reasoning": data.get("reasoning", []) or [],
            },
            status="succeeded",
        )
