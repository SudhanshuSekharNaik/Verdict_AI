import uuid
from typing import Any, Dict, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.legal_source import LegalChunk, LegalSource
from court_data.parser import CourtDocumentParser
from rag.chunking import LegalStructureChunker
from rag.embeddings import EmbeddingService


class CourtDataIngestionService:
    """Ingests, parses, chunks, and vector-indexes permitted court records."""

    @staticmethod
    async def import_court_document(
        db: AsyncSession,
        title: str,
        citation: str,
        court: str,
        year: int,
        full_text: str,
        provenance_url: str,
        jurisdiction: str = "India",
    ) -> LegalSource:
        # Check if already exists
        existing = await db.execute(select(LegalSource).where(LegalSource.citation == citation))
        if existing.scalars().first():
            return existing.scalars().first()

        # Parse structural sections
        analyzed = CourtDocumentParser.analyze_court_document(full_text)

        source = LegalSource(
            title=title,
            citation=citation,
            court=court or analyzed.get("court", "High Court"),
            year=year,
            jurisdiction=jurisdiction,
            source_type="PRECEDENT",
            full_text=full_text,
            summary=analyzed.get("reasoning_ratio", full_text[:400]),
            provenance_url=provenance_url,
            metadata_json=analyzed,
        )
        db.add(source)
        await db.flush()

        # Structure-aware chunking & embedding
        chunks_data = LegalStructureChunker.chunk_legal_document(
            text=full_text, source_metadata={"citation": citation, "court": court, "year": year}
        )

        for c in chunks_data:
            emb = EmbeddingService.embed_text(c["chunk_text"])
            legal_chunk = LegalChunk(
                source_id=source.id,
                chunk_index=c["chunk_index"],
                section_type=c["section_type"],
                chunk_text=c["chunk_text"],
                embedding=emb,
                metadata_json=c,
            )
            db.add(legal_chunk)

        await db.commit()
        await db.refresh(source)
        return source
