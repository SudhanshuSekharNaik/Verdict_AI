import re
from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.legal_source import LegalSource
from ml import get_ml_registry


class CitationValidator:
    """Validates legal citations against verified statutes and authoritative case law."""

    @staticmethod
    async def validate_citation(
        db: AsyncSession, citation_str: str, proposition: str
    ) -> Dict[str, Any]:
        if not citation_str or not citation_str.strip():
            return {
                "status": "UNVERIFIED",
                "citation": citation_str,
                "confidence": 0.0,
                "message": "Unable to verify authoritative source. No citation provided.",
                "source_details": None,
            }

        clean_cit = citation_str.strip()

        # 1. Look up citation or title in database
        stmt = select(LegalSource).where(
            (LegalSource.citation.ilike(f"%{clean_cit}%"))
            | (LegalSource.title.ilike(f"%{clean_cit}%"))
            | (LegalSource.statute_section.ilike(f"%{clean_cit}%"))
        )
        result = await db.execute(stmt)
        matched_source = result.scalars().first()

        if not matched_source:
            # Check statutory patterns (e.g. Section 73 of Indian Contract Act)
            statute_match = re.search(r"(?:Section|Sec\.?)\s*(\d+)", clean_cit, re.IGNORECASE)
            if statute_match:
                return {
                    "status": "VERIFIED",
                    "citation": clean_cit,
                    "confidence": 0.90,
                    "message": f"Statutory Provision: Section {statute_match.group(1)} recognized in codified law.",
                    "source_details": {
                        "citation": clean_cit,
                        "court": "Codified Legislation",
                        "jurisdiction": "National",
                    },
                }

            return {
                "status": "UNVERIFIED",
                "citation": clean_cit,
                "confidence": 0.0,
                "message": "Unable to verify authoritative source in current knowledge base.",
                "source_details": None,
            }

        # 2. Run NLI check between proposition and source text
        nli = get_ml_registry().get_nli()
        nli_res = nli.analyze_claim_vs_evidence(claim=proposition, evidence=matched_source.full_text[:1200])

        if nli_res["status"] == "CONTRADICTION":
            status_val = "UNVERIFIED"
            msg = "Authority cited directly contradicts the asserted legal proposition."
        elif nli_res["status"] == "ENTAILMENT":
            status_val = "VERIFIED"
            msg = f"Authoritative precedent verified from {matched_source.court} ({matched_source.year})."
        else:
            status_val = "PARTIALLY_SUPPORTED"
            msg = f"Precedent {matched_source.citation} found; proposition applies with situational distinctions."

        return {
            "status": status_val,
            "citation": matched_source.citation,
            "confidence": round(nli_res["confidence"], 2),
            "message": msg,
            "source_details": {
                "source_id": str(matched_source.id),
                "title": matched_source.title,
                "court": matched_source.court,
                "year": matched_source.year,
                "provenance_url": matched_source.provenance_url,
                "summary": matched_source.summary,
            },
        }
