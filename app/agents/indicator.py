"""Indicator Conceptualization Agent (Phase H).

Develops candidate indicator specifications once the standardized methodology
and SCAD requirements are understood. Indicator cards are downstream outputs —
they are not assumed to exist at intake.
"""

from __future__ import annotations

import json

from app.agent.extractor import extract_json
from app.llm.client import LLMClient
from app.models.indicator import IndicatorSpecification
from app.workflow.contracts import Agent, AgentContract, AgentResult

SYSTEM_PROMPT = """You are a statistical indicator conceptualization agent.

Develop candidate indicator specifications from a methodology. Each indicator
must have a clear name (English and Arabic), definition, unit, population,
frequency, data sources, classifications, derivation rule, and quality
considerations. Ground every indicator in the methodology; do not invent
indicators that the methodology does not support.

Return valid JSON only."""

USER_TEMPLATE = """Indicator development context:

Objective: {objective}

Standardized methodology:
{standardized}

SCAD current practice (from input analysis):
{scad_practice}

Clarification answers:
{clarification}

Identify the candidate indicators and produce full specifications. Return JSON
with this shape:
{{
  "indicators": [
    {{
      "code": "IND-001",
      "name": "English name",
      "name_ar": "Arabic name",
      "definition": "...",
      "unit": "...",
      "population": "...",
      "numerator": "...",
      "denominator": "...",
      "frequency": "...",
      "data_sources": ["..."],
      "classifications": ["..."],
      "derivation_rule": "...",
      "quality_considerations": "...",
      "source_refs": ["methodology section or standard"]
    }}
  ],
  "traceability": [
    {{"indicator": "English name", "methodology_section": "...", "source_ref": "..."}}
  ],
  "reasoning": ["2-4 concise step-by-step thoughts"]
}}

Provide at most 6 indicators. Keep the response compact so it fits the output
limit."""


class IndicatorConceptualizationAgent(Agent):
    contract = AgentContract(
        id="indicator_agent",
        version="1.0",
        purpose="Develop candidate indicator specifications from the methodology.",
        input_schema={
            "objective": "string",
            "standardized_methodology": "object",
            "scad_input_analysis": "object",
            "clarification": "object",
        },
        output_schema={"indicators": "list", "traceability": "list"},
        approval_required=False,
        can_modify_case=False,
        can_propose_case_updates=True,
    )

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, inputs: dict) -> AgentResult:
        objective = (inputs or {}).get("objective") or ""
        standardized = (inputs or {}).get("standardized_methodology") or {}
        methodology = standardized.get("methodology") or {}
        scad_input = (inputs or {}).get("scad_input_analysis") or {}
        clarification = (inputs or {}).get("clarification") or {}

        standardized_text = "\n".join(
            f"{s.get('number')}. {s.get('title')}: {s.get('content', '')}"
            for s in methodology.get("sections", [])
        )
        scad_text = "\n".join(
            f"- {c.get('dimension', '')}: {c.get('scad_practice', '')}"
            for c in scad_input.get("current_practice", [])
        )
        clarification_text = "\n".join(
            f"- {q.get('question', '')}" for q in clarification.get("question_set", [])
        )

        user_prompt = USER_TEMPLATE.format(
            objective=objective or "statistical indicator",
            standardized=standardized_text or "(none)",
            scad_practice=scad_text or "(none)",
            clarification=clarification_text or "(none)",
        )

        try:
            raw = self._llm.chat(SYSTEM_PROMPT, user_prompt, max_tokens=2500)
            data = json.loads(extract_json(raw))
        except Exception as exc:  # noqa: BLE001
            return AgentResult(
                agent_id=self.contract.id,
                status="failed",
                recommendations=[{"error": f"indicator output invalid: {exc}"}],
            )

        indicators = [
            IndicatorSpecification(**item).model_dump()
            for item in data.get("indicators", [])
            if item.get("name")
        ]

        return AgentResult(
            agent_id=self.contract.id,
            outputs={
                "indicators": indicators,
                "traceability": data.get("traceability", []) or [],
                "reasoning": data.get("reasoning", []) or [],
            },
            status="succeeded",
        )
