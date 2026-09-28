from app.agent.terminology import canonicalize, detect_language, is_arabic


def test_detect_arabic():
    assert detect_language("نريد مؤشر شهري للمنشآت النشطة") == "ar"


def test_detect_english():
    assert detect_language("We need a monthly indicator.") == "en"


def test_detect_mixed():
    assert detect_language("نريد monthly indicator عن active establishments") == "mixed"


def test_is_arabic():
    assert is_arabic("منشأة")
    assert not is_arabic("establishment")


def test_canonicalize_arabic_terms():
    assert "monthly indicator" in canonicalize("مؤشر شهري")
    assert "establishment" in canonicalize("منشأة")
    assert "business register" in canonicalize("السجل التجاري")
    assert "statistical unit" in canonicalize("الوحدة الإحصائية")


def test_analyze_arabic_input(make_agent):
    agent = make_agent()
    result = agent.analyze("نريد مؤشر شهري للمنشآت النشطة.")
    assert not result.get("parse_error")
    assert result["extraction"]["indicators"][0]["value"] == "active establishments"
    assert result["extraction"]["frequencies"][0]["value"] == "monthly"
    assert result["recommended_question"]["question"]


def test_analyze_english_input(make_agent):
    agent = make_agent()
    result = agent.analyze("We need a monthly indicator of active establishments.")
    assert not result.get("parse_error")
    assert result["extraction"]["indicators"][0]["value"] == "active establishments"


def test_analyze_mixed_input(make_agent):
    agent = make_agent()
    result = agent.analyze("نريد نطلع monthly indicator عن active establishments.")
    assert not result.get("parse_error")
    assert result["extraction"]["indicators"][0]["value"] == "active establishments"


def test_bilingual_inputs_produce_english_question(make_agent):
    agent = make_agent()
    for text in (
        "نريد مؤشر شهري للمنشآت النشطة.",
        "We need a monthly indicator of active establishments.",
        "نريد monthly indicator عن active establishments.",
    ):
        result = agent.analyze(text)
        question = result["recommended_question"]["question"]
        assert question
        # Questions must be formulated in English.
        assert not any("\u0600" <= ch <= "\u06FF" for ch in question)


def test_analyze_handles_parse_failure(make_agent):
    agent = make_agent(["not valid json"])
    result = agent.analyze("نريد مؤشر شهري.")
    assert result.get("parse_error") is True
