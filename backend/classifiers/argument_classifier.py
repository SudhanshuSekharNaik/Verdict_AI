from functools import lru_cache
from typing import Dict, Any

ARGUMENT_TYPES = [
    "factual evidence",
    "legal precedent",
    "procedural objection",
    "emotional appeal",
    "character testimony",
    "expert opinion",
]

STRENGTH_LABELS = [
    "strong and well-supported",
    "moderate",
    "weak and unsupported",
]

_pipeline_available = True
try:
    from transformers import pipeline
except Exception:
    _pipeline_available = False


@lru_cache(maxsize=1)
def _get_classifier():
    if not _pipeline_available:
        return None
    try:
        return pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    except Exception:
        return None


def classify_argument_type(text: str) -> str:
    clf = _get_classifier()
    if clf:
        try:
            result = clf(text, candidate_labels=ARGUMENT_TYPES)
            return result["labels"][0]
        except Exception:
            pass
    # Resilient fallback classifier
    text_lower = text.lower()
    if any(k in text_lower for k in ["section", "bns", "bsa", "bnss", "act", "precedent", "statute", "article"]):
        return "legal precedent"
    if any(k in text_lower for k in ["cctv", "dna", "fingerprint", "exhibit", "record", "timestamp", "log", "fact"]):
        return "factual evidence"
    if any(k in text_lower for k in ["expert", "forensic", "medical", "doctor", "post-mortem"]):
        return "expert opinion"
    if any(k in text_lower for k in ["objection", "leading", "hearsay", "relevance"]):
        return "procedural objection"
    return "factual evidence"


def classify_argument_strength(text: str) -> str:
    clf = _get_classifier()
    if clf:
        try:
            result = clf(text, candidate_labels=STRENGTH_LABELS)
            return result["labels"][0]
        except Exception:
            pass
    # Resilient fallback classifier
    if len(text.split()) > 25 and ("section" in text.lower() or "exhibit" in text.lower() or "fact" in text.lower()):
        return "strong and well-supported"
    return "moderate"


def annotate(text: str) -> dict:
    """Runs both classifiers on a single argument and returns their tags together."""
    return {
        "argument_type": classify_argument_type(text),
        "argument_strength": classify_argument_strength(text),
    }
