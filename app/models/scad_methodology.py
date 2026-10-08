"""SCAD-specific methodology schema (Phase I).

The SCAD methodology document structure (7 sections, matching SCAD's official
documents such as the Literacy Statistics Methodology). Content carries the
SCAD annotation conventions inline: ``[Aligned with: source]``,
``[Abu Dhabi exception]``, and ``[To be confirmed by SCAD]`` (rendered red
italic in the DOCX).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

SCAD_SECTIONS: list[tuple[str, str]] = [
    ("1", "Introduction"),
    ("2", "Statistical Information"),
    ("3", "Statistical Processing"),
    ("4", "Methodology Changes"),
    ("5", "Revision Policy"),
    ("6", "Statistical Quality"),
    ("7", "Appendix Table"),
]

SCAD_SUBSECTION_GUIDE = """Section 2 (Statistical Information) must include these subsections:
2.1 Importance and Objectives; 2.2 Key Outputs; 2.3 Concepts and Definitions;
2.4 Classifications and Standards Applied; 2.5 Available Breakdown;
2.6 Statistical Population; 2.7 Statistical Unit; 2.8 Geographic Coverage;
2.9 Unit of Measure; 2.10 Reference Period; 2.11 Timeliness;
2.12 Frequency of Dissemination; 2.13 Data Time Series;
2.14 Abu Dhabi Special Considerations.
Section 3 (Statistical Processing) must include these subsections:
3.1 Data Sources (3.1.1 Survey Data, 3.1.2 Administrative Data);
3.2 Data Validation and Editing (3.2.1 Data Validation, 3.2.2 Missing Data
Adjustments); 3.3 Statistical Calculation Method; 3.4 Seasonal Adjustment."""


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
