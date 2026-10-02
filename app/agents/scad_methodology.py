"""SCAD-Specific Methodology Development Agent (Phase I).

Develops the final SCAD-specific methodology by adapting the standardized
methodology to SCAD's actual current practice, incorporating confirmed answers
and approved indicator specifications. Applies the SCAD annotation conventions.
"""

from __future__ import annotations

import json

from app.agent.extractor import extract_json
from app.llm.client import LLMClient
from app.models.scad_methodology import SCAD_SECTIONS, SCADMethodology, SCADSection
from app.workflow.contracts import Agent, AgentContract, AgentResult

SYSTEM_PROMPT = """You are a statistical methodology documentation agent.

Produce the final SCAD-specific methodology document. Reflect SCAD's ACTUAL
current practices (not the international ideal), using the standardized
methodology, the SCAD current-practice analysis, clarification answers, and
approved indicator specifications.

Apply these annotation conventions inline:
- "[Aligned with: <source>]" where SCAD practice matches an international standard.
- "[Abu Dhabi exception]" with justification where SCAD deviates.
- "[To be confirmed by SCAD]" for anything unconfirmed (fill from international
  best practice rather than leaving blank).

Write formal, objective English prose. Return valid JSON only."""

USER_TEMPLATE = """Methodology context:

Objective: {objective}

Standardized methodology:
{standardized}

SCAD current practice:
{scad_practice}

Clarification answers:
{clarification}

Approved indicator specifications:
{indicators}

Produce the SCAD-specific methodology covering these sections:
{sections}

For each section write formal prose paragraphs. Return JSON with this shape:
{{
  "sections": [
    {{"number": "1", "title": "Introduction", "content": "..."}},
    ...
  ],
  "source_refs": ["..."],
  "indicator_codes": ["IND-001", "..."],
  "reasoning": ["2-4 concise step-by-step thoughts"]
}}

Keep the response compact so it fits the output limit."""


class SCADMethodologyAgent(Agent):
    contract = AgentContract(
        id="scad_methodology_agent",
        version="1.0",
        purpose="Develop the final SCAD-specific methodology document.",
        input_schema={
            "objective": "string",
            "standardized_methodology": "object",
            "scad_input_analysis": "object",
            "clarification": "object",
            "indicator_development": "object",
        },
        output_schema={"methodology": "object", "source_refs": "list", "indicator_codes": "list"},
        approval_required=True,
        can_modify_case=False,
        can_propose_case_updates=True,
    )

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, inputs: dict) -> AgentResult:
        objective = (inputs or {}).get("objective") or ""
        standardized = (inputs or {}).get("standardized_methodology") or {}
        scad_input = (inputs or {}).get("scad_input_analysis") or {}
        clarification = (inputs or {}).get("clarification") or {}
        indicators = (inputs or {}).get("indicator_development") or {}

        methodology = standardized.get("methodology") or {}
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
        indicator_text = "\n".join(
            f"- {i.get('code', '')} {i.get('name', '')}: {i.get('definition', '')}"
            for i in indicators.get("indicators", [])
        )

        user_prompt = USER_TEMPLATE.format(
            objective=objective or "statistical indicator",
            standardized=standardized_text or "(none)",
            scad_practice=scad_text or "(none)",
            clarification=clarification_text or "(none)",
            indicators=indicator_text or "(none)",
            sections="\n".join(f"{n}. {t}" for n, t in SCAD_SECTIONS),
        )

        try:
            raw = self._llm.chat(SYSTEM_PROMPT, user_prompt, max_tokens=2500)
            data = json.loads(extract_json(raw))
        except Exception as exc:  # noqa: BLE001
            return AgentResult(
                agent_id=self.contract.id,
                status="failed",
                recommendations=[{"error": f"scad methodology output invalid: {exc}"}],
            )

        by_number = {
            s.get("number"): s for s in data.get("sections", []) if s.get("number")
        }
        sections = [
            SCADSection(
                number=num,
                title=title,
                content=(by_number.get(num) or {}).get("content", ""),
            )
            for num, title in SCAD_SECTIONS
        ]

        methodology_doc = SCADMethodology(
            title=f"{objective or 'Statistical Indicator'} — Statistical Methodology",
            sections=sections,
            source_refs=data.get("source_refs", []) or [],
            indicator_codes=data.get("indicator_codes", []) or [],
        )

        return AgentResult(
            agent_id=self.contract.id,
            outputs={
                "methodology": methodology_doc.model_dump(),
                "source_refs": methodology_doc.source_refs,
                "indicator_codes": methodology_doc.indicator_codes,
                "reasoning": data.get("reasoning", []) or [],
            },
            status="succeeded",
        )
