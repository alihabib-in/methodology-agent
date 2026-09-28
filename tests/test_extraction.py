import json

import pytest

from app.agent.extractor import Extractor, extract_json
from app.models.extraction import ExtractionResult
from tests.conftest import DEFAULT_RESPONSE, FakeLLM


def test_extract_json_strips_markdown_fence():
    raw = '```json\n{"a": 1}\n```'
    assert extract_json(raw) == '{"a": 1}'


def test_extract_json_ignores_trailing_text():
    raw = 'Here is the result: {"a": 1} and some more text'
    assert extract_json(raw) == '{"a": 1}'


def test_extract_json_handles_nested_braces():
    raw = '{"a": {"b": 1}, "c": [1, 2, 3]} trailing'
    assert extract_json(raw) == '{"a": {"b": 1}, "c": [1, 2, 3]}'


def test_extractor_returns_validated_result():
    extractor = Extractor(FakeLLM())
    result = extractor.extract("نريد مؤشر شهري للمنشآت النشطة.")
    assert isinstance(result, ExtractionResult)
    assert result.language == "ar"
    assert result.indicators[0].value == "active establishments"


def test_extractor_retries_on_invalid_json():
    responses = [
        "not json at all",
        DEFAULT_RESPONSE,
    ]
    extractor = Extractor(FakeLLM(responses))
    result = extractor.extract("some text")
    assert isinstance(result, ExtractionResult)
    assert result.summary == "Monthly active establishment indicator"


def test_extractor_rejects_malformed_data():
    responses = ["not json at all"]
    extractor = Extractor(FakeLLM(responses))
    with pytest.raises(ValueError):
        extractor.extract("some text")
