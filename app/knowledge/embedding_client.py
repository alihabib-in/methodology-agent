"""HTTP client for the standalone embedding service (runtime-agnostic).

Mirrors LLMClient: the application only depends on ``embed``, never on
sentence-transformers, torch, CPU or GPU specifics.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings


class EmbeddingError(RuntimeError):
    pass


class EmbeddingClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.embedding_url).rstrip("/")

    def embed(self, texts: list[str], task: str = "passage") -> list[list[float]]:
        payload = {"texts": texts, "task": task}
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(f"{self.base_url}/embed", json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise EmbeddingError(f"Embedding request failed: {exc}") from exc

        return data.get("vectors", [])

    def embed_query(self, text: str) -> list[float]:
        return self.embed([text], task="query")[0]

    def embed_document(self, text: str) -> list[float]:
        return self.embed([text], task="passage")[0]

    def health(self) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/health")
                response.raise_for_status()
                data = response.json()
            return {
                "available": True,
                "model": data.get("model"),
                "dimension": data.get("dimension"),
            }
        except httpx.HTTPError:
            return {"available": False, "model": None, "dimension": None}
