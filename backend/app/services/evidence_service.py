import hashlib
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.evidence import Evidence, EvidencePartyEnum, EvidenceStatusEnum
from app.models.evidence_chunk import EvidenceChunk
from app.schemas.evidence import EvidenceCreate
from app.services.timeline_service import TimelineService
from document_ai.parser import DocumentParser
from ml import get_ml_registry


class EvidenceService:
    @staticmethod
    async def process_and_store_evidence(
        db: AsyncSession,
        case_id: uuid.UUID,
        metadata: EvidenceCreate,
        file: UploadFile,
        uploaded_by_id: Optional[uuid.UUID] = None,
    ) -> Evidence:
        content = await file.read()
        file_hash = DocumentParser.calculate_hash(content)

        file_extension = Path(file.filename).suffix if file.filename else ".bin"
        safe_filename = f"{case_id}_{file_hash[:12]}{file_extension}"
        file_path = settings.UPLOAD_DIR / safe_filename
        file_path.write_bytes(content)

        # Parse document content
        parsed_doc = DocumentParser.parse_file(file_path, mime_type=file.content_type)
        extracted_text = parsed_doc.get("full_text", "")
        page_count = parsed_doc.get("page_count", 1)

        # ML Classification & NER extraction
        registry = get_ml_registry()
        doc_classification = {"label": metadata.document_type, "confidence": 0.5}
        entities = []
        
        if extracted_text.strip():
            classifier = registry.get_classifier()
            doc_classification = classifier.classify_document(extracted_text[:1500])
            ner = registry.get_ner()
            entities = ner.extract_entities(extracted_text[:1500])

        extraction_metadata = {
            "original_filename": file.filename,
            "content_type": file.content_type,
            "file_size_bytes": len(content),
            "page_count": page_count,
            "ai_classification": doc_classification,
            "legal_entities": entities,
            "disclaimer": "FICTIONAL DEMO DOCUMENT — NOT A REAL LEGAL RECORD",
        }

        # Store Evidence Record
        db_evidence = Evidence(
            case_id=case_id,
            party=metadata.party,
            title=metadata.title,
            document_type=doc_classification["label"] if doc_classification["confidence"] > 0.65 else metadata.document_type,
            source=metadata.source,
            verification_status=EvidenceStatusEnum.INDEXED,
            file_hash=file_hash,
            file_path=str(file_path),
            mime_type=file.content_type,
            file_size=len(content),
            uploaded_by=uploaded_by_id,
            extraction_metadata=extraction_metadata,
            extracted_text=extracted_text,
        )
        db.add(db_evidence)
        await db.flush()

        # Chunk and Index
        chunks = [extracted_text[i : i + 500] for i in range(0, len(extracted_text), 450)]
        for idx, chunk_str in enumerate(chunks):
            if chunk_str.strip():
                chunk_obj = EvidenceChunk(
                    evidence_id=db_evidence.id,
                    chunk_index=idx,
                    chunk_text=chunk_str.strip(),
                    embedding=[],  # Will be embedded during RAG indexing
                    metadata_json={"page": (idx // 2) + 1, "char_len": len(chunk_str)},
                )
                db.add(chunk_obj)

        # Auto-extract timeline events from document text
        # Date regex scanner
        import re
        date_matches = re.findall(
            r"\b(?:\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})\b",
            extracted_text,
            re.IGNORECASE,
        )
        if date_matches:
            for dm in date_matches[:3]:
                await TimelineService.extract_and_register_event(
                    db=db,
                    case_id=case_id,
                    date_raw_str=dm,
                    title=f"Record: {metadata.title}",
                    description=f"Event evidenced in {metadata.title}",
                    party=metadata.party.value,
                    source_evidence_id=db_evidence.id,
                )

        await db.commit()
        await db.refresh(db_evidence)
        return db_evidence

    @staticmethod
    async def get_case_evidence(db: AsyncSession, case_id: uuid.UUID) -> List[Evidence]:
        result = await db.execute(
            select(Evidence)
            .where(Evidence.case_id == case_id)
            .options(selectinload(Evidence.chunks))
            .order_by(Evidence.created_at.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_evidence_by_id(db: AsyncSession, evidence_id: uuid.UUID) -> Optional[Evidence]:
        result = await db.execute(
            select(Evidence)
            .where(Evidence.id == evidence_id)
            .options(selectinload(Evidence.chunks))
        )
        return result.scalars().first()
