"""Retrieval-augmented knowledge (RAG) — Phase 7.

Question -> Embedding -> Qdrant -> relevant methodology knowledge -> LLM.

Only approved/published knowledge is indexed, so retrieval never surfaces
unvalidated candidates.
"""

from __future__ import annotations

import uuid

from app.knowledge.embedding_client import EmbeddingClient
from app.knowledge.vector_store import VectorStore

embedding = EmbeddingClient()
store = VectorStore()


def ensure_index(dimension: int | None = None) -> None:
    dim = dimension or embedding.health().get("dimension") or 384
    store.ensure_collection(dim)


def index_knowledge(
    item_id: str,
    concept: str,
    statement: str,
    domain: str | None = None,
) -> str:
    vector = embedding.embed_document(statement)
    ensure_index(len(vector))
    point_id = str(uuid.uuid4())
    payload = {
        "knowledge_id": item_id,
        "concept": concept,
        "domain": domain,
        "statement": statement,
    }
    store.upsert([point_id], [vector], [payload])
    return point_id


def retrieve(query: str, limit: int = 5) -> list[dict]:
    try:
        vector = embedding.embed_query(query)
        hits = store.search(vector, limit=limit)
    except Exception:  # noqa: BLE001 - retrieval is best-effort, never fatal
        return []

    results = []
    for hit in hits:
        payload = hit.payload or {}
        results.append(
            {
                "knowledge_id": payload.get("knowledge_id"),
                "concept": payload.get("concept"),
                "domain": payload.get("domain"),
                "statement": payload.get("statement"),
                "score": round(float(hit.score), 4),
            }
        )
    return results
