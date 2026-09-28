"""Multilingual embedding via sentence-transformers (optional dependency).

Runs on CPU by default (the LLM owns most of the 4 GB GPU). The model is
selected per the spec: an open multilingual model evaluated on Arabic/English
methodology terminology, not by generic MTEB ranking alone.
"""

from __future__ import annotations

from app.core.config import settings


class Embedder:
    def __init__(self, model_name: str | None = None, device: str = "cpu") -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Install it with: pip install -r requirements-embed.txt"
            ) from exc

        self.model = SentenceTransformer(
            model_name or settings.embedding_model,
            device=device,
        )

    @property
    def dimension(self) -> int:
        if hasattr(self.model, "get_embedding_dimension"):
            return int(self.model.get_embedding_dimension())
        return int(self.model.get_sentence_embedding_dimension())

    def embed(self, texts: str | list[str]) -> list[list[float]]:
        if isinstance(texts, str):
            texts = [texts]
        vectors = self.model.encode(texts, normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]
