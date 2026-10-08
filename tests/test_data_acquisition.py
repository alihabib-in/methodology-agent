from app.agents.data_acquisition import _topic_queries
from app.research.portals.worldbank import _score


def test_topic_queries_word_boundary_not_substring():
    # "ai" is a substring of "detailed" and "explains" — it must NOT trigger
    # the AI-adoption queries for such unrelated text.
    queries = _topic_queries("a detailed explanation", "", "")
    assert "internet users" not in queries
    assert "broadband subscriptions" not in queries


def test_topic_queries_cpi_maps_to_cpi():
    queries = _topic_queries("Consumer Price Index in the United Arab Emirates", "", "")
    assert "consumer price index" in queries
    assert "inflation" in queries


def test_topic_queries_ai_maps_to_ai():
    queries = _topic_queries("Develop an AI Adoption Index", "", "")
    assert "internet users" in queries


def test_search_score_uses_word_boundary():
    # "net" is a substring of "internet" but is not a standalone word there,
    # so it must not match.
    assert _score("Internet users", "net") == 0
    assert _score("Individuals using the Internet", "internet") >= 1
