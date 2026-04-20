from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed(text: str) -> list[float]:
    model = _get_model()
    return model.encode(text, normalize_embeddings=True).tolist()
