"""Indicator specification schema (Phase H).

Indicator cards are downstream outputs of the methodology workflow. The schema
mirrors SCAD's "Indicator Information Card": a fixed, ordered set of metadata
fields (one indicator per column in the source spreadsheets). ``INDICATOR_CARD_FIELDS``
declares the ordered field list used when rendering the transposed card format.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# Ordered (heading, attribute) pairs matching the SCAD Indicator Information
# Card layout (column 1 = headings, one indicator per subsequent column).
INDICATOR_CARD_FIELDS: list[tuple[str, str]] = [
    ("Indicator code", "code"),
    ("Topic", "topic"),
    ("Section responsibility", "section_responsibility"),
    ("Theme", "theme"),
    ("Sub-theme(s)", "sub_theme"),
    ("Indicator name", "name"),
    ("Indicator name (Arabic)", "name_ar"),
    ("Indicator description", "description"),
    ("Importance, objective and use of indicator", "importance_objective_use"),
    ("International standards and classifications applied", "international_standards"),
    ("Available breakdown (Variables)", "available_breakdown"),
    ("Special aggregates", "special_aggregates"),
    ("Keywords", "keywords"),
    ("Statistical population", "statistical_population"),
    ("Geographic coverage", "geographic_coverage"),
    ("Reference period", "reference_period"),
    ("Release date", "release_date"),
    ("Measurement unit", "measurement_unit"),
    ("Scale", "scale"),
    ("Base period", "base_period"),
    ("Data publication frequency", "publication_frequency"),
    ("Available periodicity", "available_periodicity"),
    ("Methodology", "methodology"),
    ("Data sources", "data_sources"),
    ("Statistical calculation method", "calculation_method"),
    ("Seasonally adjusted", "seasonally_adjusted"),
    ("Chain linking", "chain_linking"),
    ("Time series", "time_series"),
    ("Data coherence and comparability", "data_coherence_comparability"),
    ("Data validation & editing", "data_validation_editing"),
    ("Data accuracy & potential sources of errors", "data_accuracy_errors"),
    ("Last methodology revision", "last_methodology_revision"),
    ("Language of dataset, publication, and metadata", "language"),
    ("Indicator ownership", "indicator_ownership"),
    ("Focal contact for this dataset", "focal_contact"),
    ("Mode of dissemination", "mode_of_dissemination"),
    ("Data accessibility", "data_accessibility"),
    ("Target audience", "target_audience"),
    ("Last update of indicator information card", "last_update"),
    ("Additional comments & information", "additional_comments"),
    ("Indicators with common sub-theme", "indicators_with_common_sub_theme"),
    ("Copyright and usage restrictions", "copyright_usage"),
]


class IndicatorSpecification(BaseModel):
    code: str = ""
    topic: str = ""
    section_responsibility: str = ""
    theme: str = ""
    sub_theme: str = ""
    name: str = ""
    name_ar: str = ""
    description: str = ""
    importance_objective_use: str = ""
    international_standards: str = ""
    available_breakdown: str = ""
    special_aggregates: str = "N/A"
    keywords: list[str] = Field(default_factory=list)
    statistical_population: str = ""
    geographic_coverage: str = ""
    reference_period: str = ""
    release_date: str = ""
    measurement_unit: str = ""
    scale: str = "N/A"
    base_period: str = "N/A"
    publication_frequency: str = ""
    available_periodicity: str = ""
    methodology: str = "See methodologies page on SCAD's official website"
    data_sources: list[str] = Field(default_factory=list)
    calculation_method: str = ""
    seasonally_adjusted: str = "N/A"
    chain_linking: str = "N/A"
    time_series: str = ""
    data_coherence_comparability: str = ""
    data_validation_editing: str = ""
    data_accuracy_errors: str = ""
    last_methodology_revision: str = ""
    language: str = "English, Arabic"
    indicator_ownership: str = ""
    focal_contact: str = ""
    mode_of_dissemination: str = ""
    data_accessibility: str = ""
    target_audience: str = ""
    last_update: str = ""
    additional_comments: str = ""
    indicators_with_common_sub_theme: list[str] = Field(default_factory=list)
    copyright_usage: str = "© SCAD, for public usage"

    def card_row(self) -> list[str]:
        """Return the field values in SCAD card order (for the transposed layout)."""
        values: list[str] = []
        for _heading, attr in INDICATOR_CARD_FIELDS:
            value = getattr(self, attr, "")
            if isinstance(value, list):
                value = ", ".join(value)
            values.append(str(value))
        return values


class IndicatorSet(BaseModel):
    indicators: list[IndicatorSpecification] = Field(default_factory=list)
