"""SCAD Input / Current Practice Analysis Agent (Phase G).

Reads SCAD current-practice documents and maps them against the standardized
methodology, producing a current-practice assessment, a mapping matrix, and the
gaps (implemented vs missing). Findings remain sourced evidence — they are not
authoritative case facts.
"""

from __future__ import annotations

import json

from app.agent.extractor import extract_json
from app.llm.client import LLMClient
from app.workflow.contracts import Agent, AgentContract, AgentResult

SYSTEM_PROMPT = """You are a statistical methodology analysis agent.

Analyze SCAD's current-practice documents against a standardized (international
best-practice) methodology. Distinguish what SCAD actually does from what is
missing. Preserve evidence; do not invent practices that are not in the
documents.

Return valid JSON only."""

USER_TEMPLATE = """Indicator: {objective}

Standardized methodology sections (international best practice):
{standardized}

SCAD current-practice documents (extracted text):
{documents}

Produce:
1. current_practice — what SCAD currently does, per methodology dimension.
2. mapping_matrix — for each standardized section, whether SCAD practice is
   "implemented", "partial", or "missing", with a short gap note.
3. gaps — the material gaps (dimension, description, severity major/moderate/minor).
4. questions — information that still needs SCAD clarification.

Return JSON with this shape:
{{
  "current_practice": [
    {{"dimension": "...", "scad_practice": "...", "source": "filename"}}
  ],
  "mapping_matrix": [
    {{"section": "1. Conceptual Framework and Definition", "scad_status": "implemented|partial|missing", "gap": "..."}}
  ],
  "gaps": [
    {{"dimension": "...", "description": "...", "severity": "major|moderate|minor"}}
  ],
  "questions": [
    {{"question": "...", "reason": "...", "dimension": "..."}}
  ],
  "reasoning": ["2-4 concise step-by-step thoughts"]
}}"""


class SCADInputAgent(Agent):
    contract = AgentContract(
        id="scad_input_agent",
        version="1.0",
        purpose="Analyze SCAD current-practice documents against the standardized methodology.",
        input_schema={"objective": "string", "standardized_methodology": "object", "scad_documents": "list"},
        output_schema={
            "current_practice": "list",
            "mapping_matrix": "list",
            "gaps": "list",
            "questions": "list",
        },
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
        documents = (inputs or {}).get("scad_documents") or []

        sections_text = "\n".join(
            f"{s.get('number')}. {s.get('title')}\n{s.get('content', '')}"
            for s in methodology.get("sections", [])
        )
        documents_text = "\n\n".join(
            f"[document {i + 1}]\n{d}" for i, d in enumerate(documents)
        )

        user_prompt = USER_TEMPLATE.format(
            objective=objective or "statistical indicator",
            standardized=sections_text or "(none)",
            documents=documents_text or "(none)",
        )

        try:
            raw = self._llm.chat(SYSTEM_PROMPT, user_prompt, max_tokens=2500)
            data = json.loads(extract_json(raw))
        except Exception as exc:  # noqa: BLE001
            return AgentResult(
                agent_id=self.contract.id,
                status="failed",
                recommendations=[{"error": f"scad input output invalid: {exc}"}],
            )

        return AgentResult(
            agent_id=self.contract.id,
            outputs={
                "current_practice": data.get("current_practice", []) or [],
                "mapping_matrix": data.get("mapping_matrix", []) or [],
                "gaps": data.get("gaps", []) or [],
                "questions": data.get("questions", []) or [],
                "reasoning": data.get("reasoning", []) or [],
            },
            status="succeeded",
        )
