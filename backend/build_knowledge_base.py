import io
import json
import math
import os
from pathlib import Path
import re
import sys
from typing import Any, Dict, List

# Windows console UTF-8 safety
if hasattr(sys.stdout, "buffer"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

# Target root
BASE_DIR = Path(__file__).resolve().parent
KB_DIR = BASE_DIR / "knowledge_base"
INDEX_DIR = KB_DIR / "indexes"
INDEX_DIR.mkdir(parents=True, exist_ok=True)

DOMAINS = [
    "criminal_law",
    "family_law",
    "civil_law",
    "real_estate_law",
    "corporate_law",
    "cyber_law",
    "ip_law",
    "tax_law",
    "constitutional_law",
    "employment_law",
    "environmental_law",
    "human_rights_law",
    "banking_finance_law",
]

import hashlib

def compute_embedding(text: str) -> List[float]:
    """Generates a dense normalized vector using deterministic 512-dim token hashing."""
    words = re.findall(r"\b[a-zA-Z0-9_§]{2,}\b", text.lower())
    dim = 512
    vec = [0.0] * dim
    if not words:
        return vec
    for w in words:
        # Deterministic MD5 hash feature index
        h = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16) % dim
        # Bigram hashing for compound legal terms (e.g. 'grave_and_sudden', 'domestic_violence')
        vec[h] += 1.0
    
    # Also add bigrams
    for i in range(len(words) - 1):
        bigram = f"{words[i]}_{words[i+1]}"
        hb = int(hashlib.md5(bigram.encode("utf-8")).hexdigest(), 16) % dim
        vec[hb] += 1.5

    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [round(x / norm, 6) for x in vec]


def chunk_markdown_file(file_path: Path) -> List[Dict[str, Any]]:
    """Splits markdown file on natural section boundaries (### headers or structured blocks)."""
    text = file_path.read_text(encoding="utf-8")
    doc_name = file_path.stem.replace("_", " ").title()
    chunks = []

    # Split by ### headers
    raw_sections = re.split(r"(?=\n###\s+)", text)
    for sec in raw_sections:
        clean_sec = sec.strip()
        if not clean_sec:
            continue
        
        lines = clean_sec.split("\n")
        title = lines[0].replace("#", "").strip() if lines else doc_name
        
        # Word count / token estimate
        token_count = int(len(clean_sec.split()) * 1.3)
        
        chunks.append({
            "source_doc": file_path.name,
            "title": title,
            "content": clean_sec,
            "tokens": token_count,
        })

    return chunks


def build_all_domain_indexes():
    print("=" * 65)
    print("NYAY MANCH — OFFLINE RAG KNOWLEDGE BASE BUILDER")
    print("=" * 65)

    summary = {}

    for domain in DOMAINS:
        domain_path = KB_DIR / domain
        if not domain_path.exists():
            print(f"[SKIP] Domain folder missing: {domain}")
            continue

        domain_chunks = []
        md_files = sorted(list(domain_path.glob("*.md")))

        for mf in md_files:
            file_chunks = chunk_markdown_file(mf)
            for c in file_chunks:
                c["domain"] = domain
                c["vector"] = compute_embedding(f"{c['title']}\n{c['content']}")
                domain_chunks.append(c)

        out_path = INDEX_DIR / f"{domain}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({
                "domain": domain,
                "total_chunks": len(domain_chunks),
                "source_files": [mf.name for mf in md_files],
                "chunks": domain_chunks,
            }, f, indent=2, ensure_ascii=False)

        summary[domain] = len(domain_chunks)
        print(f"✓ Indexed [{domain}]: {len(domain_chunks)} chunks across {len(md_files)} files -> {out_path.name}")

    print("-" * 65)
    print(f"BUILD COMPLETE: Indexed {sum(summary.values())} total chunks across {len(summary)} domains.")
    print("=" * 65)
    return summary


if __name__ == "__main__":
    build_all_domain_indexes()
