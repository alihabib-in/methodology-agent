"""Compliance / QA Agent (Phase J).

Validates the SCAD methodology artifact for completeness, consistency,
provenance, annotations, and template requirements. Read-only: it never
modifies authoritative methodology state. Produces a QA report with blocking /
non-blocking findings and a technical approval recommendation.
"""

from __future__ import annotations

import json

from app.agent.extractor import extract_json
from app.llm.client import LLMClient
from app.models.compliance import QAFinding, QAReport
from app.workflow.contracts import Agent, AgentContract, AgentResult

SYSTEM_PROMPT = """You are a statistical methodology compliance reviewer.

Review a SCAD methodology document for completeness, internal consistency,
terminology, evidence traceability, unsupported claims, unresolved fields,
annotation compliance, and source citations. Report findings only; do not
modify the methodology.

Return valid JSON only."""

USER_TEMPLATE = """SCAD methodology document:
{methodology}

Standardized methodology (reference):
{standardized}

Return JSON with this shape:
{{
  "findings": [
    {{"severity": "blocking|non_blocking", "item": "...", "detail": "..."}}
  ],
  "summary": "one paragraph overall assessment",
  "reasoning": ["2-4 concise step-by-step thoughts"]
}}"""


class ComplianceAgent(Agent):
    contract = AgentContract(
        id="compliance_agent",
        version="1.0",
        purpose="Validate methodology outputs for completeness and compliance.",
        input_schema={"scad_methodology": "object", "standardized_methodology": "object"},
        output_schema={"qa_report": "object", "blocking_issues": "list", "non_blocking_issues": "list"},
        approval_required=False,
        can_modify_case=False,
        can_propose_case_updates=False,
    )

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, inputs: dict) -> AgentResult:
        scad_methodology = (inputs or {}).get("scad_methodology") or {}
        methodology = scad_methodology.get("methodology") or {}
        standardized = (inputs or {}).get("standardized_methodology") or {}

        sections = methodology.get("sections", [])
        source_refs = methodology.get("source_refs", [])
        checklist: list[QAFinding] = []
        blocking: list[str] = []
        non_blocking: list[str] = []

        # Deterministic checks.
        empty = [s.get("title") for s in sections if not (s.get("content") or "").strip()]
        if empty:
            blocking.append(f"Empty sections: {', '.join(empty)}")
            checklist.append(QAFinding(severity="blocking", item="section completeness", status="fail", detail=f"missing content: {empty}"))
        else:
            checklist.append(QAFinding(severity="non_blocking", item="section completeness", status="pass", detail="all sections populated"))

        if not source_refs:
            non_blocking.append("No source references cited")
            checklist.append(QAFinding(severity="non_blocking", item="source citations", status="fail", detail="no source references"))
        else:
            checklist.append(QAFinding(severity="non_blocking", item="source citations", status="pass", detail=f"{len(source_refs)} references"))

        unconfirmed = sum((s.get("content") or "").count("[To be confirmed by SCAD]") for s in sections)
        checklist.append(QAFinding(
            severity="blocking" if unconfirmed > 5 else "non_blocking",
            item="unconfirmed fields",
            status="warning" if unconfirmed else "pass",
            detail=f"{unconfirmed} items marked [To be confirmed by SCAD]",
        ))

        # LLM review.
        methodology_text = "\n".join(
            f"{s.get('number')}. {s.get('title')}: {s.get('content', '')}" for s in sections
        )
        standardized_text = "\n".join(
            f"{s.get('number')}. {s.get('title')}" for s in standardized.get("methodology", {}).get("sections", [])
        )
        try:
            raw = self._llm.chat(
                SYSTEM_PROMPT,
                USER_TEMPLATE.format(methodology=methodology_text or "(none)", standardized=standardized_text or "(none)"),
                max_tokens=1200,
            )
            data = json.loads(extract_json(raw))
            llm_findings = data.get("findings", []) or []
            summary = data.get("summary", "")
        except Exception:  # noqa: BLE001 - LLM review is advisory
            llm_findings = []
            summary = "LLM review unavailable."

        for finding in llm_findings:
            severity = finding.get("severity", "non_blocking")
            detail = finding.get("detail", "")
            item = finding.get("item", "llm review")
            if severity == "blocking":
                blocking.append(detail or item)
                checklist.append(QAFinding(severity="blocking", item=item, status="fail", detail=detail))
            else:
                non_blocking.append(detail or item)
                checklist.append(QAFinding(severity="non_blocking", item=item, status="warning", detail=detail))

        recommendation = "not_recommended" if blocking else ("changes_required" if non_blocking else "recommended")

        report = QAReport(
            checklist=checklist,
            blocking_issues=blocking,
            non_blocking_issues=non_blocking,
            approval_recommendation=recommendation,
            summary=summary,
        )

        return AgentResult(
            agent_id=self.contract.id,
            outputs={
                "qa_report": report.model_dump(),
                "blocking_issues": blocking,
                "non_blocking_issues": non_blocking,
                "approval_recommendation": recommendation,
                "reasoning": data.get("reasoning", []) or [],
            },
            status="succeeded",
        )
