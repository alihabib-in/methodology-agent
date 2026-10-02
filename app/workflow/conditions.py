"""Workflow condition facts (Phase B).

These boolean facts drive dynamic stage activation (spec §5.5/§5.6). Their
values are computed from case/source/evidence state by the relevant phases;
this module provides the known names and a safe default context.
"""

CONDITION_NAMES = [
    "scad_documents_available",
    "unresolved_scad_requirements",
    "indicators_required",
    "gap_assessment_required",
]


def default_condition_context() -> dict[str, bool]:
    """Return a context with every known condition defaulted to False."""
    return {name: False for name in CONDITION_NAMES}


def merge_conditions(*contexts: dict[str, bool]) -> dict[str, bool]:
    merged = default_condition_context()
    for context in contexts:
        merged.update(context or {})
    return merged
