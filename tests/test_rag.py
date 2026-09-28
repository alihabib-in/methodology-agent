import pytest

from app.knowledge import rag


def test_retrieve_degrades_gracefully_when_embedding_down(monkeypatch):
    class _Down:
        def embed_query(self, text):
            raise RuntimeError("embedding service unavailable")

    monkeypatch.setattr(rag, "embedding", _Down())
    assert rag.retrieve("anything") == []


def test_retrieve_degrades_gracefully_when_store_down(monkeypatch):
    class _OkEmbedding:
        def embed_query(self, text):
            return [0.1, 0.2]

    class _DownStore:
        def search(self, vector, limit=5):
            raise RuntimeError("qdrant unavailable")

    monkeypatch.setattr(rag, "embedding", _OkEmbedding())
    monkeypatch.setattr(rag, "store", _DownStore())
    assert rag.retrieve("anything") == []


def test_retrieve_returns_payloads(monkeypatch):
    class _Hit:
        def __init__(self, payload, score):
            self.payload = payload
            self.score = score

    class _OkEmbedding:
        def embed_query(self, text):
            return [0.1, 0.2]

    class _OkStore:
        def search(self, vector, limit=5):
            return [
                _Hit(
                    {"knowledge_id": "K-1", "concept": "x", "statement": "stmt"},
                    0.91,
                )
            ]

    monkeypatch.setattr(rag, "embedding", _OkEmbedding())
    monkeypatch.setattr(rag, "store", _OkStore())

    results = rag.retrieve("query")
    assert len(results) == 1
    assert results[0]["knowledge_id"] == "K-1"
    assert results[0]["score"] == pytest.approx(0.91)
