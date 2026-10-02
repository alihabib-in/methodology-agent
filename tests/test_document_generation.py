from app.agents.document_generation import render_standardized_methodology_docx
from app.models.standardized_methodology import StandardizedMethodology, StandardizedSection


def test_render_docx_produces_valid_zip():
    methodology = StandardizedMethodology(
        title="Standardized Methodology — Test",
        sections=[
            StandardizedSection(
                number="1",
                title="Conceptual Framework and Definition",
                content="Define the indicator.\n- bullet point",
            ),
        ],
    )
    data = render_standardized_methodology_docx(methodology)
    assert isinstance(data, bytes)
    assert data[:4] == b"PK\x03\x04"  # DOCX is a ZIP archive
    assert len(data) > 1000
