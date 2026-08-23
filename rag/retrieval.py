import uuid
from typing import Any, Dict, List, Optional
from rank_bm25 import BM25Okapi
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.legal_source import LegalChunk, LegalSource
from ml.similarity.sentence_embedder import SentenceEmbedder
from rag.embeddings import EmbeddingService
from rag.reranking import LegalReranker


class HybridRetriever:
    """Hybrid Keyword (BM25) + Dense Vector Retrieval with Cross-Encoder Reranking."""

    @staticmethod
    async def retrieve(
        db: AsyncSession,
        query: str,
        top_k: int = 5,
        jurisdiction: Optional[str] = None,
        court: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        # 1. Fetch all legal chunks from database
        stmt = select(LegalChunk).options(selectinload(LegalChunk.source))
        result = await db.execute(stmt)
        chunks = list(result.scalars().all())

        if not chunks:
            return []

        # Optional metadata filtering
        filtered_chunks = []
        for c in chunks:
            if court and c.source.court.lower() != court.lower():
                continue
            if jurisdiction and c.source.jurisdiction.lower() != jurisdiction.lower():
                continue
            filtered_chunks.append(c)

        if not filtered_chunks:
            filtered_chunks = chunks

        # 2. Dense Vector Scoring
        query_embedding = EmbeddingService.embed_text(query)
        vector_scores = []
        for c in filtered_chunks:
            c_emb = c.embedding if c.embedding else EmbeddingService.embed_text(c.chunk_text)
            sim = SentenceEmbedder.cosine_similarity(query_embedding, c_emb)
            vector_scores.append(sim)

        # 3. Sparse BM25 Scoring
        tokenized_corpus = [c.chunk_text.lower().split() for c in filtered_chunks]
        tokenized_query = query.lower().split()
        bm25 = BM25Okapi(tokenized_corpus)
        bm25_raw_scores = bm25.get_scores(tokenized_query)
        max_bm25 = max(bm25_raw_scores) if len(bm25_raw_scores) > 0 and max(bm25_raw_scores) > 0 else 1.0
        normalized_bm25 = [score / max_bm25 for score in bm25_raw_scores]

        # 4. Hybrid Combination (50% Vector + 50% BM25)
        candidates = []
        for i, c in enumerate(filtered_chunks):
            v_score = vector_scores[i]
            k_score = normalized_bm25[i]
            hybrid_score = (0.5 * v_score) + (0.5 * k_score)
            candidates.append({
                "chunk_id": str(c.id),
                "source_id": str(c.source.id),
                "citation": c.source.citation,
                "title": c.source.title,
                "court": c.source.court,
                "year": c.source.year,
                "section_type": c.section_type,
                "chunk_text": c.chunk_text,
                "vector_score": round(v_score, 4),
                "bm25_score": round(k_score, 4),
                "hybrid_score": round(hybrid_score, 4),
                "provenance_url": c.source.provenance_url,
            })

        # 5. Rerank top candidates
        reranked = LegalReranker.rerank(query=query, candidates=candidates, top_k=top_k)
        return reranked
