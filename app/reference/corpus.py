"""Reference corpus for SCAD's official sample documents.

``SCAD_METHODOLOGY_STYLE`` and ``INDICATOR_CARD_EXEMPLAR`` are curated fallback
exemplars. ``load_scad_methodology_style()`` reads the real SCAD methodology
document shipped alongside this module (``Literacy_Methodology_EN_2026.md``),
strips embedded images / tables / footnotes, and returns a trimmed excerpt so
the agents learn SCAD's actual tone and formatting from the source document.
"""

from __future__ import annotations

import re
from pathlib import Path

SCAD_METHODOLOGY_STYLE = """Follow SCAD's official methodology document style.

Title: "Version 1.0 / METHODOLOGY OF / <Topic> / <Year> / classified as Open".

Introduction tone (third-person, formal):
"<Topic> statistics provide an overview of ... in the Emirate of Abu Dhabi ...
SCAD compiles and disseminates official statistics to ensure the availability of
consistent, reliable, and standardized data ... This methodology document
describes the statistical framework used to produce ..., in line with
internationally recognized practices."

Structure: 1. Introduction; 2. Statistical Information (2.1 Importance and
Objectives, 2.2 Key Outputs, 2.3 Concepts and Definitions, 2.4 Classifications
and Standards Applied, 2.5 Available Breakdown, 2.6 Statistical Population,
2.7 Statistical Unit, 2.8 Geographic Coverage, 2.9 Unit of Measure,
2.10 Reference Period, 2.11 Timeliness, 2.12 Frequency of Dissemination,
2.13 Data Time Series, 2.14 Abu Dhabi Special Considerations);
3. Statistical Processing (3.1 Data Sources, 3.2 Data Validation and Editing,
3.3 Statistical Calculation Method, 3.4 Seasonal Adjustment);
4. Methodology Changes; 5. Revision Policy; 6. Statistical Quality;
7. Appendix Table."""

INDICATOR_CARD_EXEMPLAR = """Example SCAD indicator card (match this tone):
- Indicator name: Area of plant holdings in Al Dhafra region by agricultural centers
- Description: This indicator measures area of plant holdings in Al Dhafra region.
- Importance: The importance of the area of plant holdings lies in its role as a key indicator of agricultural activity.
- Statistical population: The statistical population covers all plant holdings in Al Dhafra region.
- Geographic coverage: Geographical coverage includes Al Dhafra region.
- Reference period: The reference period for the data is the previous year.
- Release date: Within 12 months after the reference period.
- Measurement unit: Donum
- Data publication frequency: Annually
- Data sources: Abu Dhabi Agriculture and Food Safety Authority"""

_REFERENCE_FILE = Path(__file__).with_name("Literacy_Methodology_EN_2026.md")

_INLINE_FOOTNOTE_RE = re.compile(r"\[\^\d+\]")


def _clean_reference(text: str) -> str:
    lines: list[str] = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s:
            continue
        if s.startswith("![]("):  # embedded base64 image
            continue
        if s.startswith("|"):  # markdown table row
            continue
        if s.startswith("[^"):  # footnote definition
            continue
        if set(s) <= set("|-: "):  # table separator
            continue
        lines.append(_INLINE_FOOTNOTE_RE.sub("", s))
    return "\n".join(lines)


def load_scad_methodology_style(limit: int = 2200) -> str:
    """Return a trimmed excerpt of the real SCAD methodology document, or the
    curated fallback if the file is missing/unreadable."""
    try:
        if _REFERENCE_FILE.exists():
            cleaned = _clean_reference(_REFERENCE_FILE.read_text(encoding="utf-8"))
            if cleaned:
                return cleaned[:limit]
    except Exception:  # noqa: BLE001 - fall back to curated exemplar
        pass
    return SCAD_METHODOLOGY_STYLE

