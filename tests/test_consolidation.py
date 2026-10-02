from app.case.consolidation import build_case_proposal


def test_build_case_proposal_maps_fields():
    outputs = {
        "summary": "Develop a methodology for measuring graduate outcomes.",
        "methodology_state": {
            "objective": {"value": "Measure graduate employment outcomes", "status": "confirmed"},
            "indicators": [{"value": "graduate employment rate"}],
            "definitions": [{"concept": "employment"}],
            "data_sources": [{"name": "administrative records"}],
            "constraints": [{"value": "budget"}],
            "open_questions": [{"note": "reference period unclear"}],
        },
        "gaps": [{"label": "Target population"}, {"label": "Reference period"}],
    }
    proposal = build_case_proposal(outputs, evidence_refs=["E-1"])
    assert proposal["objective"] == "Measure graduate employment outcomes"
    assert proposal["business_need"] == "Develop a methodology for measuring graduate outcomes."
    assert "indicator: graduate employment rate" in proposal["explicit_requirements"]
    assert proposal["constraints"] == ["budget"]
    assert proposal["missing_information"] == ["Target population", "Reference period"]
    assert proposal["ambiguities"] == ["reference period unclear"]
    assert proposal["evidence_refs"] == ["E-1"]


def test_build_case_proposal_empty_state():
    proposal = build_case_proposal({})
    assert proposal["objective"] is None
    assert proposal["explicit_requirements"] == []
    assert proposal["missing_information"] == []
