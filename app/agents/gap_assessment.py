"""Gap Assessment Agent (Phase J).

Compares the SCAD-specific methodology against the standardized (international
best-practice) methodology and produces a formal gap assessment with evidence
references.
"""

from __future__ import annotations

import json

from app.agent.extractor import extract_json
from app.llm.client import LLMClient
from app.models.gap_assessment import GapAssessment, GapItem
from app.workflow.contracts import Agent, AgentContract, AgentResult

SYSTEM_PROMPT = """You are a statistical methodology gap assessment analyst.

Compare a SCAD-specific methodology against the standardized (international
best-practice) methodology. Identify gaps by dimension, classify each gap
(None / Minor / Moderate / Major), and cite the specific standard and SCAD
practice. Provide recommendations and a compliance summary.

Return valid JSON only."""

USER_TEMPLATE = """Indicator: {objective}

Standardized methodology (international best practice):
{standardized}

SCAD-specific methodology:
{scad}

Return JSON with this shape:
{{
  "executive_summary": "...",
  "matrix": [
    {{"dimension": "...", "international_standard": "...", "scad_practice": "...",
      "gap_level": "None|Minor|Moderate|Major", "description": "...", "root_cause": "..."}}
  ],
  "priority_areas": [
    {{"priority": "High|Medium|Low", "gap_description": "...", "recommended_action": "...", "international_standard": "..."}}
  ],
  "compliance_summary": "...",
  "recommendations": ["..."],
  "references": ["..."],
  "reasoning": ["2-4 concise step-by-step thoughts"]
}}"""


class GapAssessmentAgent(Agent):
    contract = AgentContract(
        id="gap_assessment_agent",
        version="1.0",
        purpose="Compare the SCAD methodology against the standardized methodology and produce a gap assessment.",
        input_schema={"objective": "string", "standardized_methodology": "object", "scad_methodology": "object"},
        output_schema={"gap_assessment": "object", "gap_register": "list", "recommendations": "list"},
        approval_required=False,
        can_modify_case=False,
        can_propose_case_updates=True,
    )

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, inputs: dict) -> AgentResult:
        objective = (inputs or {}).get("objective") or ""
        standardized = (inputs or {}).get("standardized_methodology") or {}
        scad_methodology = (inputs or {}).get("scad_methodology") or {}

        standardized_text = "\n".join(
            f"{s.get('number')}. {s.get('title')}: {s.get('content', '')}"
            for s in standardized.get("methodology", {}).get("sections", [])
        )
        scad_text = "\n".join(
            f"{s.get('number')}. {s.get('title')}: {s.get('content', '')}"
            for s in scad_methodology.get("methodology", {}).get("sections", [])
        )

        user_prompt = USER_TEMPLATE.format(
            objective=objective or "statistical indicator",
            standardized=standardized_text or "(none)",
            scad=scad_text or "(none)",
        )

        try:
            raw = self._llm.chat(SYSTEM_PROMPT, user_prompt, max_tokens=2500)
            data = json.loads(extract_json(raw))
        except Exception as exc:  # noqa: BLE001
            return AgentResult(
                agent_id=self.contract.id,
                status="failed",
                recommendations=[{"error": f"gap assessment output invalid: {exc}"}],
            )

        matrix = [
            GapItem(**item).model_dump()
            for item in data.get("matrix", [])
            if item.get("dimension")
        ]

        gap_assessment = GapAssessment(
            executive_summary=data.get("executive_summary", "") or "",
            matrix=matrix,
            priority_areas=data.get("priority_areas", []) or [],
            compliance_summary=data.get("compliance_summary", "") or "",
            recommendations=data.get("recommendations", []) or [],
            references=data.get("references", []) or [],
        )

        gap_register = [
            {
                "dimension": g.dimension,
                "gap_level": g.gap_level,
                "description": g.description,
            }
            for g in gap_assessment.matrix
            if g.gap_level in ("Moderate", "Major")
        ]

        return AgentResult(
            agent_id=self.contract.id,
            outputs={
                "gap_assessment": gap_assessment.model_dump(),
                "gap_register": gap_register,
                "recommendations": gap_assessment.recommendations,
                "reasoning": data.get("reasoning", []) or [],
            },
            status="succeeded",
        )
