import io
import json
import math
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional

# UTF-8 safety
if hasattr(sys.stdout, "buffer"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
KB_INDEX_DIR = BASE_DIR / "knowledge_base" / "indexes"

# In-memory cache for loaded domain vector indexes
_DOMAIN_INDEX_CACHE: Dict[str, Dict[str, Any]] = {}
import hashlib

def compute_query_vector(text: str) -> List[float]:
    """Generates deterministic 512-dim token embedding for incoming query text."""
    words = re.findall(r"\b[a-zA-Z0-9_§]{2,}\b", text.lower())
    dim = 512
    vec = [0.0] * dim
    if not words:
        return vec
    for w in words:
        h = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16) % dim
        vec[h] += 1.0

    for i in range(len(words) - 1):
        bigram = f"{words[i]}_{words[i+1]}"
        hb = int(hashlib.md5(bigram.encode("utf-8")).hexdigest(), 16) % dim
        vec[hb] += 1.5

    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [round(x / norm, 6) for x in vec]


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculates cosine similarity between two normalized vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    return float(dot)


def load_domain_index(domain: str) -> Optional[Dict[str, Any]]:
    """Loads and caches domain JSON index from disk."""
    if domain in _DOMAIN_INDEX_CACHE:
        return _DOMAIN_INDEX_CACHE[domain]

    index_file = KB_INDEX_DIR / f"{domain}.json"
    if not index_file.exists():
        return None

    try:
        with open(index_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            _DOMAIN_INDEX_CACHE[domain] = data
            return data
    except Exception as e:
        print(f"[ERROR] Failed to load domain index {domain}: {e}")
        return None


def query_domain_knowledge(
    domain: str,
    query_text: str,
    top_k: int = 6,
    relevance_threshold: float = 0.10,
) -> Dict[str, Any]:
    """
    Performs domain-scoped offline RAG retrieval for an agent.
    Returns labeled reference passages and anti-hallucination directives.
    """
    index_data = load_domain_index(domain)
    if not index_data or not index_data.get("chunks"):
        return {
            "domain": domain,
            "has_strong_match": False,
            "top_similarity": 0.0,
            "retrieved_chunks": [],
            "grounding_block": (
                "RELEVANT LEGAL REFERENCE MATERIAL (retrieved for this case):\n"
                "NOTE: No domain index was found for this specialty. Reason directly from the case's canonical facts "
                "and established legal principles without fabricating unverified statute numbers or citations."
            ),
        }

    query_vec = compute_query_vector(query_text)
    scored_chunks = []

    for c in index_data["chunks"]:
        c_vec = c.get("vector")
        if not c_vec:
            continue
        sim = cosine_similarity(query_vec, c_vec)
        scored_chunks.append((sim, c))

    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    top_results = scored_chunks[:top_k]

    if not top_results:
        top_sim = 0.0
    else:
        top_sim = top_results[0][0]

    # Mismatched-pairing fallback guardrail
    if top_sim < relevance_threshold:
        return {
            "domain": domain,
            "has_strong_match": False,
            "top_similarity": top_sim,
            "retrieved_chunks": [],
            "grounding_block": (
                "RELEVANT LEGAL REFERENCE MATERIAL (retrieved for this case):\n"
                "NOTE: Top retrieved domain materials scored below relevance threshold for this specific fact pattern. "
                "Rely strictly upon the case's canonical facts, registered exhibits, and general statutory reasoning. "
                "Do NOT invent section numbers or case citations outside the factual record."
            ),
        }

    # Format authoritative citations
    passages = []
    for rank, (sim, chunk) in enumerate(top_results, start=1):
        source_label = chunk.get("title", chunk.get("source_doc", "Legal Document"))
        passages.append(
            f"--- [REFERENCE {rank}: {source_label} (Relevance: {sim:.2f})] ---\n"
            f"{chunk.get('content', '').strip()}"
        )

    grounding_block = f"""================================================================================
RELEVANT LEGAL REFERENCE MATERIAL (retrieved offline for this case):
================================================================================
{chr(10).join(passages)}
================================================================================
ANTI-HALLUCINATION & CITATION PROTOCOL:
1. Ground your legal claims and statutory references strictly in the reference material above and the case's canonical facts.
2. Cite specific sections and landmark case names explicitly when relying on them.
3. If a legal point is not covered in the retrieved material, formulate your submission using general legal doctrine and logic — NEVER fabricate, hallucinate, or guess section numbers or case names.
================================================================================"""

    return {
        "domain": domain,
        "has_strong_match": True,
        "top_similarity": top_sim,
        "retrieved_chunks": [c[1] for c in top_results],
        "grounding_block": grounding_block,
    }
