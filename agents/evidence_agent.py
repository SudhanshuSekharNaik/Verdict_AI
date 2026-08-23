import uuid
from typing import Any, Dict, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evidence import Evidence


class EvidenceAgent:
    """Evidence Agent: Manages exhibit indexing, provenance verification, and party compartmentalization."""

    @staticmethod
    async def get_party_admitted_evidence(
        db: AsyncSession, case_id: uuid.UUID, party: str
    ) -> List[Dict[str, Any]]:
        stmt = select(Evidence).where(Evidence.case_id == case_id)
        if party in ["PLAINTIFF", "DEFENDANT"]:
            stmt = stmt.where(Evidence.party == party)
        
        result = await db.execute(stmt)
        evidences = result.scalars().all()
        return [
            {
                "id": str(e.id),
                "title": e.title,
                "document_type": e.document_type,
                "party": e.party.value,
                "source": e.source,
                "verification_status": e.verification_status.value,
                "file_hash": e.file_hash,
                "extracted_text": e.extracted_text,
                "metadata": e.extraction_metadata,
            }
            for e in evidences
        ]
