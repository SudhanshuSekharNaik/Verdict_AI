from typing import Any, Dict, List
from ml import get_ml_registry


class EmbeddingService:
    """Service to generate dense embeddings for legal chunks and search queries."""

    @staticmethod
    def embed_text(text: str) -> List[float]:
        embedder = get_ml_registry().get_embedder()
        return embedder.embed_text(text)

    @staticmethod
    def embed_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        embedder = get_ml_registry().get_embedder()
        for c in chunks:
            c["embedding"] = embedder.embed_text(c["chunk_text"])
        return chunks
