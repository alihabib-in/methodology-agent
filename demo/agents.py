"""Demo agents.

Each agent implements a small, deterministic ``run()`` so the demo is fast and
repeatable. The interface mirrors the production agents (which call the LLM and
are orchestrated by the FastAPI workflow engine at ``POST /cases`` +
``/advance`` + ``/stages/{id}/approve``). To plug in the real agents, replace
``run()`` with an HTTP call to those endpoints — the orchestrator only ever
consumes the ``{"summary": ..., "questions": ..., ...}`` dictionaries returned
here.
"""

from __future__ import annotations

from typing import Any

from transcript import transcript_stats

# Keywords used by the deterministic elicitation mock. In the real system this
# is LLM extraction; here it is deliberately dumb and transparent.
_OPEN_QUESTION_HINTS = ("not confirmed", "not agreed", "need to confirm", "sign off", "define")


def _extract_case(turns: list[dict], title: str = "") -> dict:
    text = " ".join(t["text"] for t in turns)

    objective = (
        f"Develop a methodology for the {title}."
        if title
        else "Develop a methodology based on the meeting discussion."
    )

    data_sources = sorted(
        {t["text"].split(" from ")[-1].strip() for t in turns if " from " in t["text"].lower()}
    )

    open_questions = [
        t["text"]
        for t in turns
        if "?" in t["text"] or any(h in t["text"].lower() for h in _OPEN_QUESTION_HINTS)
    ]

    decisions = [
        t["text"]
        for t in turns
        if any(
            w in t["text"].lower()
            for w in ("let's", "we will", "so our", "action item", "decision")
        )
    ]

    return {
        "title": title or "Methodology Case",
        "objective": objective,
        "statistical_unit": "to be determined",
        "reference_period": "to be determined",
        "frequency": "to be determined",
        "geographic_scope": "Emirate of Abu Dhabi",
        "data_sources": data_sources,
        "breakdowns": ["sector", "size class"],
        "open_questions": open_questions,
        "decisions": decisions,
    }


class ElicitationAgent:
    """Parses the transcript into a structured meeting case (mock)."""

    name = "elicitation"
    label = "Requirement Elicitation"

    def run(self, context: dict[str, Any]) -> dict:
        turns = context["turns"]
        title = context.get("title", "")
        stats = transcript_stats(turns)
        case = _extract_case(turns, title)
        return {
            "summary": (
                f"Parsed {stats['turn_count']} turns across {stats['speaker_count']} "
                f"speakers. Objective: {case['objective']}"
            ),
            "case": case,
            "speakers": stats["speakers"],
        }


class ResearchAgent:
    name = "research"
    label = "International Research"

    def run(self, context: dict[str, Any]) -> dict:
        return {
            "summary": "Identified authoritative standards relevant to the indicator.",
            "source_register": [
                "UNSD — Principles and Recommendations for a Vital Statistics System",
                "ISIC Rev.4 — economic activity classification",
                "GSBPM v5.1 — statistical business process model",
                "IMF DQAF — data quality assessment framework",
                "Eurostat — Statistical Quality Framework",
            ],
        }


class StandardizedMethodologyAgent:
    name = "standardized"
    label = "Standardized Methodology"

    def run(self, context: dict[str, Any]) -> dict:
        case = context["case"]
        return {
            "summary": "Drafted an internationally-informed methodology (12 sections).",
            "sections": [
                "1. Conceptual Framework and Definition",
                "2. Scope and Coverage",
                "3. Units of Measurement and Reference Period",
                "4. Data Sources and Collection Methods",
                "5. Classification Systems",
                "6. Estimation and Compilation Methods",
                "7. Adjustments and Imputations",
                "8. Quality Dimensions",
                "9. Dissemination Format and Frequency",
                "10. Metadata and Documentation Requirements",
                "11. International Comparability Notes",
                "12. Known Limitations and Methodological Challenges",
            ],
            "source_refs": ["ISIC Rev.4", "GSBPM v5.1", "IMF DQAF"],
            "questions": [
                "Confirm that the definition of an active establishment aligns "
                "with the recommended international definition before proceeding."
            ],
            "objective": case["objective"],
        }


class ScadInputAgent:
    name = "scad_input"
    label = "SCAD Input Analysis"

    def run(self, context: dict[str, Any]) -> dict:
        case = context["case"]
        return {
            "summary": "Mapped SCAD current practice against the standardized methodology.",
            "current_practice": [
                {"dimension": "Data sources", "practice": "Commercial register (monthly update)"},
                {"dimension": "Reference period", "practice": "Calendar month"},
                {"dimension": "Definition of active", "practice": "Not formally standardized"},
            ],
            "gaps": ["Definition of 'active establishment' is not standardized across sources."],
        }


class ClarificationAgent:
    name = "clarification"
    label = "Clarification / Q&A"

    def run(self, context: dict[str, Any]) -> dict:
        return {
            "summary": "Generated targeted clarification questions for the remaining uncertainty.",
            "question_set": [
                "Which criterion defines an 'active' establishment in the commercial register?",
                "Should dormant-but-registered establishments be excluded?",
            ],
        }


class IndicatorAgent:
    name = "indicator"
    label = "Indicator Development"

    def run(self, context: dict[str, Any]) -> dict:
        case = context["case"]
        return {
            "summary": "Produced candidate indicator specifications (SCAD information card).",
            "indicators": [
                {
                    "code": "IND-001",
                    "name": "Number of Active Establishments",
                    "measurement_unit": "Number",
                    "publication_frequency": "Monthly",
                    "theme": "Business Statistics",
                    "description": f"This indicator measures the count of active establishments. "
                                   f"Objective: {case['objective']}",
                }
            ],
        }


class ScadMethodologyAgent:
    name = "scad_methodology"
    label = "SCAD Methodology"

    def run(self, context: dict[str, Any]) -> dict:
        case = context["case"]
        return {
            "summary": "Produced the SCAD-specific methodology document (7 sections).",
            "sections": [
                "1. Introduction",
                "2. Statistical Information",
                "3. Statistical Processing",
                "4. Methodology Changes",
                "5. Revision Policy",
                "6. Statistical Quality",
                "7. Appendix Table",
            ],
            "annotations": [
                "[Aligned with: ISIC Rev.4]",
                "[To be confirmed by SCAD] — definition of active establishment",
            ],
            "questions": [
                "Approve the SCAD-specific methodology, noting the open 'active "
                "establishment' definition requires business sign-off."
            ],
            "objective": case["objective"],
        }


class ComplianceAgent:
    name = "compliance"
    label = "Compliance / QA"

    def run(self, context: dict[str, Any]) -> dict:
        return {
            "summary": "Reviewed the methodology for completeness and consistency.",
            "blocking_issues": [],
            "non_blocking_issues": ["Definition of 'active' still marked 'To be confirmed'."],
            "approval_recommendation": "changes_required",
        }


class GapAssessmentAgent:
    name = "gap_assessment"
    label = "Gap Assessment"

    def run(self, context: dict[str, Any]) -> dict:
        return {
            "summary": "Compared SCAD practice against the standardized methodology.",
            "matrix": [
                {"dimension": "Definition of active establishment", "gap_level": "Moderate"},
                {"dimension": "Classification system (ISIC)", "gap_level": "Minor"},
            ],
            "recommendations": [
                "Standardize the 'active establishment' definition.",
                "Adopt ISIC Rev.4 for economic activity classification.",
            ],
        }


AGENTS: dict[str, Any] = {
    "elicitation": ElicitationAgent(),
    "research": ResearchAgent(),
    "standardized": StandardizedMethodologyAgent(),
    "scad_input": ScadInputAgent(),
    "clarification": ClarificationAgent(),
    "indicator": IndicatorAgent(),
    "scad_methodology": ScadMethodologyAgent(),
    "compliance": ComplianceAgent(),
    "gap_assessment": GapAssessmentAgent(),
}
