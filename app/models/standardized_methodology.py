"""Standardized methodology schema (Phase F).

The international best-practice methodology document structure, per the SCAD
`step2-template.md` (12 sections). This is a structured artifact, not a Word
document — the DOCX is generated downstream from this schema.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

STANDARDIZED_SECTIONS: list[tuple[str, str]] = [
    ("1", "Conceptual Framework and Definition"),
    ("2", "Scope and Coverage"),
    ("3", "Units of Measurement and Reference Period"),
    ("4", "Data Sources and Collection Methods"),
    ("5", "Classification Systems"),
    ("6", "Estimation and Compilation Methods"),
    ("7", "Adjustments and Imputations"),
    ("8", "Quality Dimensions"),
    ("9", "Dissemination Format and Frequency"),
    ("10", "Metadata and Documentation Requirements"),
    ("11", "International Comparability Notes"),
    ("12", "Known Limitations and Methodological Challenges"),
]


class StandardizedSection(BaseModel):
    number: str
    title: str
    content: str = ""


class StandardizedMethodology(BaseModel):
    title: str = ""
    subtitle: str = "International Best Practice Reference"
    issuing_body: str = (
        "Statistics Centre – Abu Dhabi (SCAD) — Statistical Research, "
        "Methodology & Quality Standards"
    )
    version: str = "1.0"
    sections: list[StandardizedSection] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
