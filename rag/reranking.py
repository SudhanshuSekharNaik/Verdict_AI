from typing import Any, Dict, List
import re


class LegalReranker:
    """Reranks hybrid search candidates using semantic token overlap and citation precision."""

    @staticmethod
    def rerank(query: str, candidates: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        q_terms = set(re.findall(r"\w+", query.lower()))
        legal_terms = {"section", "act", "held", "ratio", "court", "breach", "refund", "deposit", "agreement"}

        for item in candidates:
            text = item.get("chunk_text", "").lower()
            text_terms = set(re.findall(r"\w+", text))
            
            # Term overlap score
            overlap = len(q_terms.intersection(text_terms))
            overlap_score = overlap / max(len(q_terms), 1)

            # Legal keyword boost
            legal_boost = 0.15 if any(lt in text for lt in legal_terms) else 0.0
            
            # Base hybrid score
            base_score = item.get("hybrid_score", item.get("similarity", 0.5))

            final_score = (0.6 * base_score) + (0.3 * overlap_score) + legal_boost
            item["rerank_score"] = round(final_score, 4)

        # Sort by rerank score descending
        sorted_candidates = sorted(candidates, key=lambda x: x.get("rerank_score", 0.0), reverse=True)
        return sorted_candidates[:top_k]
