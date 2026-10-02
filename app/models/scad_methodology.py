"""SCAD-specific methodology schema (Phase I).

The SCAD-approved methodology document structure (9 sections per the SCAD
step5 template). Content carries the SCAD annotation conventions inline:
``[Aligned with: source]``, ``[Abu Dhabi exception]``, and
``[To be confirmed by SCAD]`` (rendered red italic in the DOCX).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

SCAD_SECTIONS: list[tuple[str, str]] = [
    ("1", "Introduction"),
    ("2", "Statistical Information"),
    ("3", "Statistical Processing"),
    ("4", "Organizational Responsibility and Production Process"),
    ("5", "Methodology Changes"),
    ("6", "Revision Policy"),
    ("7", "Statistical Quality"),
    ("8", "Dissemination and User Engagement"),
    ("9", "Appendix"),
]


class SCADSection(BaseModel):
    number: str
    title: str
    content: str = ""


class SCADMethodology(BaseModel):
    title: str = ""
    version: str = "1.0"
    classification: str = "Internal"
    sections: list[SCADSection] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    indicator_codes: list[str] = Field(default_factory=list)
