"""Indicator Conceptualization Agent (Phase H).

Develops candidate indicator specifications once the standardized methodology
and SCAD requirements are understood. Indicators are generated in SCAD's
"Indicator Information Card" format: a fixed, ordered set of metadata fields
mirroring how SCAD publishes its indicator list.
"""

from __future__ import annotations

import json

from app.agent.extractor import chat_json
from app.llm.client import LLMClient
from app.models.indicator import IndicatorSpecification
from app.reference.corpus import INDICATOR_CARD_EXEMPLAR
from app.workflow.contracts import Agent, AgentContract, AgentResult

SYSTEM_PROMPT = """You are a statistical indicator conceptualization agent for SCAD
(Statistics Centre - Abu Dhabi).

Develop candidate indicator specifications from a methodology. Each indicator
must be grounded in the methodology; do not invent indicators that the
methodology does not support.

Format each indicator as a complete SCAD "Indicator Information Card" using the
fields listed below, following these content patterns exactly:

- description: "This indicator measures ..." (one or two sentences).
- importance_objective_use: "The importance of ... lies in its role ..." or
  "This indicator tracks/monitors ...".
- international_standards: cite the authoritative standard/manual and, when
  known, its official URL; otherwise "To be determined".
- available_breakdown: "Broken down by <dimension>: • <item> • <item>" or "N/A".
- special_aggregates, scale, base_period, seasonally_adjusted, chain_linking:
  use "N/A" unless the indicator genuinely requires a value (e.g. an index uses
  a base period).
- statistical_population: "The statistical population covers ...".
- geographic_coverage: "Geographical coverage includes ...".
- reference_period: "The reference period for the data is ...".
- release_date: "Within N months after the reference period".
- measurement_unit: "Number", "Percent", "Index (2024=100)", "Donum", etc.
- publication_frequency / available_periodicity: "Annual", "Monthly",
  "Quarterly", etc.
- methodology: "See methodologies page on SCAD's official website".
- data_sources: name the actual source organisation(s).
- calculation_method: the formula / derivation rule.
- time_series: "Dataset starts from YYYY" or "To be determined".
- data_coherence_comparability / data_validation_editing / data_accuracy_errors:
  use short SCAD-standard quality boilerplate.
- last_methodology_revision / last_update: "To be determined".
- language: "English, Arabic".
- indicator_ownership / focal_contact: "Statistics Centre - Abu Dhabi (SCAD)".
- mode_of_dissemination: "SCAD website".
- data_accessibility: "PDF, MS Excel".
- target_audience: "General Public" or "Government Agencies".
- additional_comments: "<<SCAD to complete - add any additional specific
  information SCAD considers important>>".
- indicators_with_common_sub_theme: related indicator names (array).
- copyright_usage: "© SCAD, for public usage".

Here is an example of a filled SCAD indicator card — match its tone and level of
detail exactly:

""" + INDICATOR_CARD_EXEMPLAR + """
Return valid JSON only."""

USER_TEMPLATE = """Indicator development context:

Objective: {objective}

Standardized methodology:
{standardized}

SCAD current practice (from input analysis):
{scad_practice}

Clarification answers:
{clarification}

Identify the candidate indicators (at most 2) and produce a full SCAD
"Indicator Information Card" for each. Return JSON with this shape:

{{
  "indicators": [
    {{
      "code": "IND-001",
      "topic": "...",
      "section_responsibility": "...",
      "theme": "...",
      "sub_theme": "...",
      "name": "English name",
      "name_ar": "Arabic name",
      "description": "This indicator measures ...",
      "importance_objective_use": "...",
      "international_standards": "...",
      "available_breakdown": "Broken down by ...: • ... • ..." ,
      "special_aggregates": "N/A",
      "keywords": ["..."],
      "statistical_population": "The statistical population covers ...",
      "geographic_coverage": "Geographical coverage includes ...",
      "reference_period": "The reference period for the data is ...",
      "release_date": "Within ... after the reference period",
      "measurement_unit": "...",
      "scale": "N/A",
      "base_period": "N/A",
      "publication_frequency": "Annual",
      "available_periodicity": "Annual",
      "methodology": "See methodologies page on SCAD's official website",
      "data_sources": ["..."],
      "calculation_method": "...",
      "seasonally_adjusted": "N/A",
      "chain_linking": "N/A",
      "time_series": "To be determined",
      "data_coherence_comparability": "...",
      "data_validation_editing": "...",
      "data_accuracy_errors": "...",
      "last_methodology_revision": "To be determined",
      "language": "English, Arabic",
      "indicator_ownership": "Statistics Centre - Abu Dhabi (SCAD)",
      "focal_contact": "Statistics Centre - Abu Dhabi (SCAD)",
      "mode_of_dissemination": "SCAD website",
      "data_accessibility": "PDF, MS Excel",
      "target_audience": "General Public",
      "last_update": "To be determined",
      "additional_comments": "<<SCAD to complete>>",
      "indicators_with_common_sub_theme": ["..."],
      "copyright_usage": "© SCAD, for public usage"
    }}
  ],
  "traceability": [
    {{"indicator": "English name", "methodology_section": "...", "source_ref": "..."}}
  ],
  "reasoning": ["2-4 concise step-by-step thoughts"]
}}

Keep each free-text field to at most one short sentence so the response stays
compact. Return valid JSON only."""

_LIST_FIELDS = ("keywords", "data_sources", "indicators_with_common_sub_theme")


def _coerce_lists(item: dict) -> dict:
    for field in _LIST_FIELDS:
        value = item.get(field)
        if isinstance(value, str):
            item[field] = [value] if value else []
        elif not isinstance(value, list):
            item[field] = []
    return item


class IndicatorConceptualizationAgent(Agent):
    contract = AgentContract(
        id="indicator_agent",
        version="1.0",
        purpose="Develop candidate indicator specifications in SCAD's Indicator Information Card format.",
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

        if not objective:
            return AgentResult(
                agent_id=self.contract.id,
                status="failed",
                recommendations=[{"error": "missing objective in case context"}],
            )

        standardized_text = "\n".join(
            f"{s.get('number')}. {s.get('title')}: {(s.get('content', '') or '')[:120]}"
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
            objective=objective,
            standardized=standardized_text or "(none)",
            scad_practice=scad_text or "(none)",
            clarification=clarification_text or "(none)",
        )

        try:
            data = chat_json(self._llm, SYSTEM_PROMPT, user_prompt, max_tokens=2200)
        except Exception as exc:  # noqa: BLE001
            return AgentResult(
                agent_id=self.contract.id,
                status="failed",
                recommendations=[{"error": f"indicator output invalid: {exc}"}],
            )

        indicators = [
            IndicatorSpecification(**_coerce_lists(item)).model_dump()
            for item in data.get("indicators", [])
            if item.get("name") or item.get("code")
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
