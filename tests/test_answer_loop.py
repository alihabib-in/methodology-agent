from app.models.methodology_state import MethodologyState


def test_answer_updates_state(make_agent):
    agent = make_agent()

    first = agent.analyze(
        "We need a monthly indicator of active establishments.",
        use_rag=False,
    )
    assert not first.get("parse_error")
    state = MethodologyState.model_validate(first["methodology_state"])

    answer = agent.answer(
        "An active establishment is one that filed economic activity "
        "in the reference period.",
        state,
        use_rag=False,
    )
    assert not answer.get("parse_error")
    assert "methodology_state" in answer


def test_analyze_with_seed_state_accumulates(make_agent):
    agent = make_agent()

    result = agent.analyze(
        "نريد مؤشر شهري للمنشآت النشطة.",
        use_rag=False,
    )
    state = MethodologyState.model_validate(result["methodology_state"])
    assert state.indicators, "expected indicators to be extracted"

    # Re-analyze using the previous state as the seed (session continuation).
    result2 = agent.analyze(
        "البيانات من السجل التجاري.",
        state=state,
        use_rag=False,
    )
    assert not result2.get("parse_error")
    assert result2["methodology_state"]["indicators"]


def test_rag_disabled_skips_retrieval(make_agent):
    agent = make_agent()
    result = agent.analyze("We need a monthly indicator.", use_rag=False)
    assert result.get("relevant_knowledge") == []
