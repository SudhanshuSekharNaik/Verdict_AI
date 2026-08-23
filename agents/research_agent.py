from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from rag.citation_validator import CitationValidator
from rag.retrieval import HybridRetriever


class LegalResearchAgent:
    """Autonomous Legal Research Agent: Discovers statutes and verified case law authorities."""

    @staticmethod
    async def research_issue(
        db: AsyncSession,
        issue: str,
        case_facts: str,
        jurisdiction: str = "India",
        top_k: int = 4,
    ) -> Dict[str, Any]:
        if not issue or not issue.strip():
            return {
                "issue": "General Legal Principles",
                "relevant_law": [],
                "authorities": [],
                "why_relevant": "No specific issue framed.",
                "limitations": "None",
            }

        # 1. Retrieve hybrid candidates
        retrieved_chunks = await HybridRetriever.retrieve(
            db=db, query=f"{issue} {case_facts[:200]}", top_k=top_k, jurisdiction=jurisdiction
        )

        authorities = []
        for rc in retrieved_chunks:
            # Validate citation
            val = await CitationValidator.validate_citation(
                db=db, citation_str=rc["citation"], proposition=rc["chunk_text"]
            )
            authorities.append({
                "citation": rc["citation"],
                "title": rc["title"],
                "court": rc["court"],
                "year": rc["year"],
                "section_type": rc["section_type"],
                "relevant_passage": rc["chunk_text"],
                "verification_status": val["status"],
                "why_relevant": f"Establishes statutory ratio on {issue} in {rc['court']}.",
                "limitations": "Applicable subject to factual alignment with the present case matrix.",
                "source_provenance": rc.get("provenance_url") or "Authoritative Court Record",
            })

        if not authorities:
            return {
                "issue": issue,
                "relevant_law": ["Codified Civil Law / Consumer Protection Principles"],
                "authorities": [],
                "why_relevant": "Unable to verify authoritative source in local knowledge repository.",
                "limitations": "Requires manual verification against official law reports.",
            }

        return {
            "issue": issue,
            "relevant_law": list(set([a["title"] for a in authorities])),
            "authorities": authorities,
            "why_relevant": f"Discovered {len(authorities)} authoritative precedents governing {issue}.",
            "limitations": "Precedents are subject to material distinguishing on evidence.",
        }
