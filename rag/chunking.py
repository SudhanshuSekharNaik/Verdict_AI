import re
from typing import Any, Dict, List


class LegalStructureChunker:
    """Structure-Aware Legal Chunker for judicial judgments and statutory enactments."""

    SECTION_PATTERNS = [
        ("FACTS", r"(?:FACTS|FACTUAL\s+MATRIX|BACKGROUND|CASE\s+OF\s+THE\s+PROSECUTION|PLAINTIFF'S\s+CASE)"),
        ("ISSUES", r"(?:ISSUES|QUESTIONS\s+FOR\s+CONSIDERATION|POINTS\s+FOR\s+DETERMINATION)"),
        ("ARGUMENTS", r"(?:SUBMISSIONS|ARGUMENTS|CONTENTIONS\s+OF\s+THE\s+PARTIES)"),
        ("RATIO_DECIDENDI", r"(?:RATIO|REASONING|CONSIDERATION\s+AND\s+FINDINGS|DISCUSSION|LAW\s+ON\s+THE\s+POINT)"),
        ("FINAL_ORDER", r"(?:ORDER|CONCLUSION|DECISION|RESULT|DISPOSAL|DECREE)"),
    ]

    @classmethod
    def chunk_legal_document(cls, text: str, source_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not text or not text.strip():
            return []

        chunks: List[Dict[str, Any]] = []
        
        # Split document by paragraphs or section headers
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        current_section = "HEADNOTE"

        for idx, para in enumerate(paragraphs):
            # Check if this paragraph starts a new structural section
            for sec_name, pattern in cls.SECTION_PATTERNS:
                if re.search(r"^\s*(?:\d+[\.\)]\s*)?" + pattern, para, re.IGNORECASE):
                    current_section = sec_name
                    break

            # Preserve pinpoint reference
            chunks.append({
                "chunk_index": idx,
                "section_type": current_section,
                "chunk_text": para,
                "citation": source_metadata.get("citation", "Unknown"),
                "court": source_metadata.get("court", "Unknown"),
                "year": source_metadata.get("year"),
                "char_length": len(para),
            })

        return chunks
