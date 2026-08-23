from typing import Any, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession

from ml import get_ml_registry
from rag.citation_validator import CitationValidator


class ValidationAgent:
    """🛡️ Citation & Claim Validation Agent: Guards against hallucinations and unsupported assertions."""

    @staticmethod
    async def validate_argument_payload(
        db: AsyncSession,
        claim: str,
        reasoning: str,
        evidence_passages: List[str],
        citations: List[str],
    ) -> Dict[str, Any]:
        # 1. Verify Claim Grounding against Evidence
        nli = get_ml_registry().get_nli()
        grounding_res = nli.verify_grounding(claim=claim, evidence_passages=evidence_passages)

        # 2. Verify Citations
        validated_citations = []
        for cit in citations:
            val = await CitationValidator.validate_citation(db=db, citation_str=cit, proposition=reasoning)
            validated_citations.append(val)

        is_valid = grounding_res["grounding_status"] in ["SUPPORTED", "PARTIALLY_SUPPORTED"]

        return {
            "is_valid": is_valid,
            "grounding_status": grounding_res["grounding_status"],
            "grounding_confidence": grounding_res["confidence"],
            "grounding_details": grounding_res,
            "citations_validation": validated_citations,
            "requires_flag": not is_valid or any(c["status"] == "UNVERIFIED" for c in validated_citations),
        }
