from app.agents.request_detector import detect_methodology_request


def test_explicit_english_request():
    r = detect_methodology_request(
        "We need SCAD to develop a methodology for measuring graduate employment outcomes."
    )
    assert r.is_methodology_request is True
    assert r.confidence >= 0.9


def test_explicit_arabic_request():
    r = detect_methodology_request("نحتاج إلى تطوير منهجية إحصائية لقياس المنشآت النشطة")
    assert r.is_methodology_request is True


def test_weak_topics_only():
    r = detect_methodology_request("Let's talk about the indicator definition and data source frequency.")
    assert r.is_methodology_request is True
    assert r.confidence < 0.9


def test_not_a_methodology_request():
    r = detect_methodology_request("Let's schedule the next team lunch for Thursday.")
    assert r.is_methodology_request is False
