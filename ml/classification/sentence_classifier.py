from typing import Any, Dict, List


class LegalSentenceClassifier:
    """Classifies individual legal sentences into structural rhetorical roles."""

    LABELS = [
        "FACT",
        "CLAIM",
        "COUNTERCLAIM",
        "ARGUMENT",
        "EVIDENCE_REFERENCE",
        "LEGAL_PROPOSITION",
        "COURT_FINDING",
        "PROCEDURAL_EVENT",
        "ORDER",
        "UNKNOWN",
    ]

    def classify_sentence(self, sentence: str) -> Dict[str, Any]:
        s = sentence.strip()
        lower = s.lower()

        if not s:
            return {"label": "UNKNOWN", "confidence": 0.0}

        if any(k in lower for k in ["hereby ordered", "ordered accordingly", "petition dismissed", "suit decreed", "appeal allowed"]):
            return {"label": "ORDER", "confidence": 0.98}
        elif any(k in lower for k in ["section", "article", "held that", "laid down", "settled law", "precedent", "ratio"]):
            return {"label": "LEGAL_PROPOSITION", "confidence": 0.95}
        elif any(k in lower for k in ["exhibit", "annexure", "receipt", "document shows", "whatsapp message", "invoice dated"]):
            return {"label": "EVIDENCE_REFERENCE", "confidence": 0.94}
        elif any(k in lower for k in ["plaintiff contends", "submitted by plaintiff", "claimant asserts", "demands refund"]):
            return {"label": "CLAIM", "confidence": 0.91}
        elif any(k in lower for k in ["respondent denies", "defendant submits", "countered that", "in defence"]):
            return {"label": "COUNTERCLAIM", "confidence": 0.91}
        elif any(k in lower for k in ["therefore", "because", "demonstrates that", "it is submitted that", "clearly establishes"]):
            return {"label": "ARGUMENT", "confidence": 0.88}
        elif any(k in lower for k in ["on 01", "on 15", "in 2024", "on 30", "rented", "purchased", "entered into"]):
            return {"label": "FACT", "confidence": 0.89}
        elif any(k in lower for k in ["court finds", "this bench observes", "we are of the view", "it is evident"]):
            return {"label": "COURT_FINDING", "confidence": 0.93}

        return {"label": "FACT", "confidence": 0.75}

    def classify_sentences(self, sentences: List[str]) -> List[Dict[str, Any]]:
        return [self.classify_sentence(s) for s in sentences]
