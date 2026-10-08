"""Standardized Methodology Development Agent (Phase F).

Synthesizes the international research into a generic, internationally informed
methodology (the "ideal" methodology, independent of SCAD constraints). Ends at
a human approval gate (the workflow marks this stage approval_required).
"""

from __future__ import annotations

import json

from app.agent.extractor import chat_json
from app.llm.client import LLMClient
from app.models.standardized_methodology import (
    STANDARDIZED_SECTIONS,
    StandardizedMethodology,
    StandardizedSection,
)
from app.workflow.contracts import Agent, AgentContract, AgentResult


def _data_text(datasets: list[dict]) -> str:
    """Render retrieved datasets as a compact block for the LLM prompt."""
    if not datasets:
        return "- (no real data retrieved)"
    lines = []
    for d in datasets:
        latest = d.get("latest") or []
        if d.get("portal") == "worldbank":
            sample = "; ".join(f"{v.get('year', '?')}: {v.get('value')}" for v in latest[:3])
        else:
            sample = f"{d.get('data_points', len(latest))} data points"
        lines.append(f"- [{d['portal']}] {d.get('title')} ({d.get('dataset_id')}): {sample}")
    return "\n".join(lines)


SYSTEM_PROMPT = """You are a statistical methodology development agent.

Develop a comprehensive STANDARDIZED methodology representing international
best practice for a statistical indicator. Use only verified international
standards (UN, UNSD, UNECE, ILO, OECD, IMF, World Bank, Eurostat, SDMX,
GCC-Stat). Write formal, objective English. Do not include SCAD-specific
implementation details.

Return valid JSON only."""

USER_TEMPLATE = """Indicator / objective: {objective}
Domain: {domain}

Relevant international sources:
{sources}

Key research findings:
{findings}

Real data retrieved from public portals (cite these figures factually, do not
invent numbers):
{data}

Develop the standardized methodology covering these sections:
{sections}

For each section write 2-4 formal sentences reflecting international best
practice. Return JSON with this shape:
{{
  "sections": [
    {{"number": "1", "title": "Conceptual Framework and Definition", "content": "..."}},
    ...
  ],
  "source_refs": ["IRIIP 2010", "ISIC Rev.4", "..."],
  "reasoning": ["2-4 concise step-by-step thoughts"]
}}

Keep the whole response compact so it fits in the output limit."""


class StandardizedMethodologyAgent(Agent):
    contract = AgentContract(
        id="standardized_methodology_agent",
        version="1.0",
        purpose="Develop a generic, internationally informed standardized methodology.",
        input_schema={"objective": "string", "domain": "string", "international_research": "object"},
        output_schema={"methodology": "object", "source_refs": "list"},
        approval_required=True,
        can_modify_case=False,
        can_propose_case_updates=True,
    )

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, inputs: dict) -> AgentResult:
        objective = (inputs or {}).get("objective") or ""
        domain = (inputs or {}).get("domain") or ""
        research = (inputs or {}).get("international_research") or {}

        if not objective:
            return AgentResult(
                agent_id=self.contract.id,
                status="failed",
                recommendations=[{"error": "missing objective in case context"}],
            )

        source_names = [
            s.get("name") for s in research.get("source_register", []) if s.get("name")
        ]
        findings = research.get("findings", []) or []
        findings_text = "\n".join(
            f"- {f.get('concept', '')}: {f.get('guidance', '')}" for f in findings
        )
        data_acq = (inputs or {}).get("data_acquisition") or {}
        datasets = data_acq.get("datasets") or data_acq.get("evidence_package", {}).get("datasets") or []
        data_text = _data_text(datasets)

        user_prompt = USER_TEMPLATE.format(
            objective=objective,
            domain=domain or "not specified",
            sources="\n".join(f"- {n}" for n in source_names) or "- (none)",
            findings=findings_text or "- (none)",
            data=data_text,
            sections="\n".join(f"{n}. {t}" for n, t in STANDARDIZED_SECTIONS),
        )

        try:
            data = chat_json(self._llm, SYSTEM_PROMPT, user_prompt, max_tokens=2500)
        except Exception as exc:  # noqa: BLE001
            return AgentResult(
                agent_id=self.contract.id,
                status="failed",
                recommendations=[{"error": f"standardized methodology output invalid: {exc}"}],
            )

        by_number = {
            s.get("number"): s for s in data.get("sections", []) if s.get("number")
        }
        sections = [
            StandardizedSection(
                number=num,
                title=title,
                content=(by_number.get(num) or {}).get("content", ""),
            )
            for num, title in STANDARDIZED_SECTIONS
        ]

        methodology = StandardizedMethodology(
            title=f"Standardized Methodology — {objective or 'Statistical Indicator'}",
            sections=sections,
            source_refs=data.get("source_refs", []) or [],
        )

        return AgentResult(
            agent_id=self.contract.id,
            outputs={
                "methodology": methodology.model_dump(),
                "source_refs": methodology.source_refs,
                "reasoning": data.get("reasoning", []) or [],
            },
            status="succeeded",
        )
