from typing import List
import numpy as np


class SentenceEmbedder:
    """Sentence embedding generator using Sentence-Transformers with fallback."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self._initialized = False

    def _lazy_init(self):
        if not self._initialized:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self.model_name)
            except Exception:
                self.model = None
            self._initialized = True

    def embed_text(self, text: str) -> List[float]:
        if not text:
            return [0.0] * 384

        self._lazy_init()
        if self.model:
            try:
                emb = self.model.encode(text)
                return [float(x) for x in emb.tolist()]
            except Exception:
                pass

        # Deterministic feature hashing fallback producing a normalized 384-dim vector
        vec = np.zeros(384, dtype=np.float32)
        words = text.lower().split()
        for w in words:
            h = hash(w) % 384
            vec[h] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return [float(x) for x in vec.tolist()]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        a = np.array(vec_a, dtype=np.float32)
        b = np.array(vec_b, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
