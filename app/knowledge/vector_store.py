"""Qdrant vector store for approved methodology knowledge (optional dependency).

Architecture (spec): Question -> Embedding -> Qdrant -> relevant knowledge
-> LLM -> context-aware answer/question.
"""

from __future__ import annotations

from app.core.config import settings


class VectorStore:
    def __init__(self, url: str | None = None, collection: str | None = None) -> None:
        try:
            from qdrant_client import QdrantClient
        except ImportError as exc:
            raise ImportError(
                "qdrant-client is not installed. Install it with: pip install -r requirements.txt"
            ) from exc

        self.client = QdrantClient(url=url or settings.qdrant_url)
        self.collection = collection or settings.qdrant_collection

    def health(self) -> dict:
        try:
            collections = self.client.get_collections()
            names = [c.name for c in collections.collections]
            return {"available": True, "collections": names}
        except Exception as exc:  # noqa: BLE001
            return {"available": False, "error": str(exc)}

    def ensure_collection(self, dimension: int) -> None:
        from qdrant_client.models import Distance, VectorParams

        if self.client.collection_exists(self.collection):
            return
        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
        )

    def upsert(self, ids: list, vectors: list[list[float]], payloads: list[dict]) -> None:
        from qdrant_client.models import PointStruct

        points = [
            PointStruct(id=point_id, vector=vector, payload=payload)
            for point_id, vector, payload in zip(ids, vectors, payloads)
        ]
        self.client.upsert(collection_name=self.collection, points=points)

    def search(self, vector: list[float], limit: int = 5) -> list:
        return self.client.search(
            collection_name=self.collection,
            query_vector=vector,
            limit=limit,
        )
