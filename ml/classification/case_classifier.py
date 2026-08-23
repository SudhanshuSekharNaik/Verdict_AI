from typing import Any, Dict, List


class DocumentClassifier:
    """Zero-Shot Legal Case and Document Classifier."""

    def __init__(self, model_name: str = "facebook/bart-large-mnli"):
        self.model_name = model_name
        self.classifier = None
        self._initialized = False

        self.case_labels = [
            "CIVIL",
            "CRIMINAL",
            "CONSUMER",
            "EMPLOYMENT",
            "PROPERTY",
            "CONTRACT",
            "FAMILY",
            "FINANCIAL",
            "TECHNOLOGY",
            "OTHER",
        ]
        self.document_labels = [
            "JUDGMENT",
            "ORDER",
            "PETITION",
            "AFFIDAVIT",
            "NOTICE",
            "CONTRACT",
            "INVOICE",
            "BANK_RECORD",
            "MESSAGE",
            "INSPECTION_REPORT",
            "OTHER",
        ]

    def _lazy_init(self):
        if not self._initialized:
            try:
                from transformers import pipeline
                self.classifier = pipeline("zero-shot-classification", model=self.model_name)
            except Exception:
                self.classifier = None
            self._initialized = True

    def classify_case(self, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {"label": "CIVIL", "confidence": 0.5, "model_version": self.model_name}

        self._lazy_init()
        if self.classifier:
            try:
                result = self.classifier(text[:1200], candidate_labels=self.case_labels)
                return {
                    "label": result["labels"][0],
                    "confidence": float(result["scores"][0]),
                    "all_scores": dict(zip(result["labels"], [float(s) for s in result["scores"]])),
                    "model_version": self.model_name,
                }
            except Exception:
                pass

        # Rule-based fallback
        lower = text.lower()
        if any(k in lower for k in ["deposit", "tenant", "landlord", "rent", "lease", "eviction"]):
            return {"label": "PROPERTY", "confidence": 0.92, "model_version": "heuristic-rule-v1"}
        elif any(k in lower for k in ["consumer", "product", "laptop", "warranty", "refund", "defective", "car", "buyer", "seller"]):
            return {"label": "CONSUMER", "confidence": 0.90, "model_version": "heuristic-rule-v1"}
        elif any(k in lower for k in ["salary", "employee", "employer", "termination", "severance", "misconduct", "workplace"]):
            return {"label": "EMPLOYMENT", "confidence": 0.93, "model_version": "heuristic-rule-v1"}
        elif any(k in lower for k in ["payment", "invoice", "advance", "transaction", "bank", "loan", "promissory"]):
            return {"label": "FINANCIAL", "confidence": 0.89, "model_version": "heuristic-rule-v1"}
        elif any(k in lower for k in ["agreement", "contract", "breach", "clause", "terms"]):
            return {"label": "CONTRACT", "confidence": 0.88, "model_version": "heuristic-rule-v1"}

        return {"label": "CIVIL", "confidence": 0.80, "model_version": "heuristic-rule-v1"}

    def classify_document(self, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {"label": "OTHER", "confidence": 0.5, "model_version": self.model_name}

        self._lazy_init()
        if self.classifier:
            try:
                result = self.classifier(text[:1000], candidate_labels=self.document_labels)
                return {
                    "label": result["labels"][0],
                    "confidence": float(result["scores"][0]),
                    "model_version": self.model_name,
                }
            except Exception:
                pass

        # Rule-based fallback
        lower = text.lower()
        if any(k in lower for k in ["agreement", "lease deed", "contract"]):
            return {"label": "CONTRACT", "confidence": 0.94, "model_version": "heuristic-v1"}
        elif any(k in lower for k in ["invoice", "tax invoice", "bill", "receipt", "total:"]):
            return {"label": "INVOICE", "confidence": 0.95, "model_version": "heuristic-v1"}
        elif any(k in lower for k in ["whatsapp", "chat", "message", "sms"]):
            return {"label": "MESSAGE", "confidence": 0.92, "model_version": "heuristic-v1"}
        elif any(k in lower for k in ["inspection", "condition report", "damage report"]):
            return {"label": "INSPECTION_REPORT", "confidence": 0.91, "model_version": "heuristic-v1"}
        elif any(k in lower for k in ["bank statement", "transaction ref", "neft", "rtgs", "upi"]):
            return {"label": "BANK_RECORD", "confidence": 0.96, "model_version": "heuristic-v1"}
        elif any(k in lower for k in ["judgment", "in the high court", "supreme court", "coram:"]):
            return {"label": "JUDGMENT", "confidence": 0.97, "model_version": "heuristic-v1"}

        return {"label": "NOTICE", "confidence": 0.75, "model_version": "heuristic-v1"}
