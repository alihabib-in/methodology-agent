"""Deterministic case consolidation (Phase C).

Converts an elicitation agent's structured outputs (methodology state, gaps,
summary) into a ``MethodologyCase`` proposal. This is the "Case Consolidation
Agent" logic implemented deterministically — overlap/merge and conflict
detection reuse the existing status taxonomy rather than an LLM black box.
"""

from __future__ import annotations


def _field_value(state: dict, field: str):
    return (state.get(field) or {}).get("value")


def build_case_proposal(outputs: dict, evidence_refs: list[str] | None = None) -> dict:
    state = outputs.get("methodology_state") or {}
    summary = outputs.get("summary") or ""
    gaps = outputs.get("gaps") or []

    objective = _field_value(state, "objective") or summary or None

    explicit_requirements: list[str] = []
    for item in state.get("indicators", []):
        value = item.get("value") or item.get("concept")
        if value:
            explicit_requirements.append(f"indicator: {value}")
    for item in state.get("definitions", []):
        concept = item.get("concept")
        if concept:
            explicit_requirements.append(f"definition: {concept}")
    for item in state.get("data_sources", []):
        name = item.get("name") or item.get("concept")
        if name:
            explicit_requirements.append(f"data source: {name}")
    for item in state.get("constraints", []):
        value = item.get("value") or item.get("concept")
        if value:
            explicit_requirements.append(f"constraint: {value}")

    constraints = [
        c.get("value") or c.get("concept")
        for c in state.get("constraints", [])
        if (c.get("value") or c.get("concept"))
    ]
    missing_information = [
        g.get("label") or g.get("domain") for g in gaps if (g.get("label") or g.get("domain"))
    ]
    ambiguities = [
        oq.get("note") or oq.get("concept")
        for oq in state.get("open_questions", [])
        if (oq.get("note") or oq.get("concept"))
    ]

    return {
        "objective": objective,
        "business_need": summary or objective,
        "explicit_requirements": explicit_requirements,
        "constraints": constraints,
        "missing_information": missing_information,
        "ambiguities": ambiguities,
        "evidence_refs": evidence_refs or [],
    }
