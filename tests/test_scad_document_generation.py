from app.agents.document_generation import render_scad_methodology_docx, review_docx
from app.models.scad_methodology import SCADMethodology, SCADSection


def test_render_and_review_scad_docx():
    methodology = SCADMethodology(
        title="Population — Statistical Methodology",
        sections=[
            SCADSection(number="1", title="Introduction", content="Background text.\n- bullet [To be confirmed by SCAD]"),
            SCADSection(number="2", title="Statistical Information", content="Definitions."),
        ],
        source_refs=["IRIIP 2010"],
    )
    data = render_scad_methodology_docx(methodology)
    assert data[:4] == b"PK\x03\x04"

    review = review_docx(data, expected_sections=["1. Introduction", "2. Statistical Information"])
    assert review["missing_sections"] == []
    assert review["unconfirmed_count"] >= 1
