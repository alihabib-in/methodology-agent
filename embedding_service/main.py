"""Standalone multilingual embedding service (sentence-transformers).

Exposes an HTTP API so the methodology API does not need to load a heavy
PyTorch model. Runs on CPU (the LLM owns the GPU). The model is selected for
Arabic/English methodology terminology, not by generic MTEB ranking.
"""

import os

from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")

model = SentenceTransformer(MODEL, device=DEVICE)
DIMENSION = int(
    model.get_embedding_dimension()
    if hasattr(model, "get_embedding_dimension")
    else model.get_sentence_embedding_dimension()
)

app = FastAPI(title="Embedding Service", version="0.1.0")


class EmbedRequest(BaseModel):
    texts: list[str]
    task: str = "passage"  # "passage" for documents, "query" for queries


@app.get("/health")
def health():
    return {"status": "healthy", "model": MODEL, "dimension": DIMENSION}


@app.post("/embed")
def embed(req: EmbedRequest):
    prefix = "query: " if req.task == "query" else "passage: "
    vectors = model.encode([prefix + t for t in req.texts], normalize_embeddings=True)
    return {
        "vectors": [v.tolist() for v in vectors],
        "dimension": DIMENSION,
    }
