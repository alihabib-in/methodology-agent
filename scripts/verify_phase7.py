"""Verify Phase 7 prerequisites: PostgreSQL, Qdrant, and the embedding model.

Usage:
    python scripts/verify_phase7.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main():
    print("=== PostgreSQL ===")
    from app.core.db import check_connection

    result = check_connection()
    if result["available"]:
        print(f"  OK  {result['version']}")
    else:
        print(f"  FAIL  {result.get('error')}")
        return

    print("\n=== Qdrant ===")
    from app.knowledge.vector_store import VectorStore

    store = VectorStore()
    health = store.health()
    if not health["available"]:
        print(f"  FAIL  {health.get('error')}")
        return
    print(f"  OK  collections={health['collections']}")

    print("\n=== Embedding model ===")
    from app.knowledge.embeddings import Embedder

    embedder = Embedder()
    print(f"  dimension = {embedder.dimension}")

    samples = [
        "How should an establishment be defined as active?",
        "ما هو تعريف المنشأة النشطة؟",
        "composite indicator of artificial intelligence adoption",
    ]
    vectors = embedder.embed(samples)
    print(f"  embedded {len(samples)} samples (dim={len(vectors[0])})")

    import numpy as np

    a = np.array(vectors[0])
    b = np.array(vectors[1])
    sim = float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))
    print(f"  cosine(EN question, AR question) = {sim:.3f}")

    store.ensure_collection(embedder.dimension)
    print(f"  collection '{store.collection}' ready")

    store.upsert(
        ids=[1, 2],
        vectors=[vectors[0], vectors[2]],
        payloads=[{"text": samples[0]}, {"text": samples[2]}],
    )
    hits = store.search(vectors[1], limit=1)
    if hits:
        print(f"  search(AR question) -> top hit: {hits[0].payload['text']}")

    print("\nPhase 7 prerequisites: OK")


if __name__ == "__main__":
    main()
