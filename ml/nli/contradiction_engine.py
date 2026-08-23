from typing import Any, Dict, List, Optional


class ContradictionEngine:
    """NLI Contradiction and Claim Grounding Engine using RoBERTa-MNLI and semantic heuristics."""

    def __init__(self, model_name: str = "roberta-large-mnli"):
        self.model_name = model_name
        self.nli = None
        self._initialized = False

    def _lazy_init(self):
        if not self._initialized:
            try:
                from transformers import pipeline
                self.nli = pipeline("text-classification", model=self.model_name, top_k=None)
            except Exception:
                self.nli = None
            self._initialized = True

    def analyze_claim_vs_evidence(self, claim: str, evidence: str) -> Dict[str, Any]:
        if not claim or not evidence:
            return {"status": "NEUTRAL", "confidence": 0.5, "all_scores": {"NEUTRAL": 1.0}}

        self._lazy_init()
        if self.nli:
            try:
                input_text = f"{evidence[:800]} </s></s> {claim[:400]}"
                results = self.nli(input_text)[0]
                scores = {r["label"].upper(): float(r["score"]) for r in results}

                contradiction_score = scores.get("CONTRADICTION", 0.0)
                entailment_score = scores.get("ENTAILMENT", 0.0)
                neutral_score = scores.get("NEUTRAL", 0.0)

                status = "NEUTRAL"
                confidence = neutral_score
                if contradiction_score > 0.55:
                    status = "CONTRADICTION"
                    confidence = contradiction_score
                elif entailment_score > 0.55:
                    status = "ENTAILMENT"
                    confidence = entailment_score

                return {
                    "status": status,
                    "confidence": float(confidence),
                    "all_scores": scores,
                    "model_version": self.model_name,
                }
            except Exception:
                pass

        # Robust Semantic Heuristic Fallback
        c_lower = claim.lower()
        e_lower = evidence.lower()

        # Check direct negative polarities / numeric contradictions
        is_contradiction = False
        contradiction_confidence = 0.0

        # Numeric contradiction (e.g. claim ₹50,000 deducted vs invoice ₹35,000 or vice versa)
        import re
        c_nums = re.findall(r"\b\d+[\d,]*\b", c_lower)
        e_nums = re.findall(r"\b\d+[\d,]*\b", e_lower)

        if ("not" in c_lower and "not" not in e_lower and any(w in e_lower for w in c_lower.split() if len(w) > 4)):
            is_contradiction = True
            contradiction_confidence = 0.85
        elif any(k in c_lower for k in ["undamaged", "pristine", "accident free", "brand new", "no damage"]) and any(k in e_lower for k in ["damage", "dent", "broken", "refurbished", "repair invoice", "repainted"]):
            is_contradiction = True
            contradiction_confidence = 0.94
        elif any(k in c_lower for k in ["refund", "returned", "paid"]) and any(k in e_lower for k in ["withheld", "deducted", "refused", "unpaid"]):
            is_contradiction = True
            contradiction_confidence = 0.91

        if is_contradiction:
            return {
                "status": "CONTRADICTION",
                "confidence": contradiction_confidence,
                "all_scores": {"CONTRADICTION": contradiction_confidence, "NEUTRAL": 1.0 - contradiction_confidence, "ENTAILMENT": 0.05},
                "model_version": "semantic-heuristic-v1",
            }

        # Check entailment
        shared_keywords = set(c_lower.split()).intersection(set(e_lower.split()))
        content_words = [w for w in shared_keywords if len(w) > 3]
        if len(content_words) >= 3:
            return {
                "status": "ENTAILMENT",
                "confidence": 0.88,
                "all_scores": {"ENTAILMENT": 0.88, "NEUTRAL": 0.10, "CONTRADICTION": 0.02},
                "model_version": "semantic-heuristic-v1",
            }

        return {
            "status": "NEUTRAL",
            "confidence": 0.80,
            "all_scores": {"NEUTRAL": 0.80, "ENTAILMENT": 0.10, "CONTRADICTION": 0.10},
            "model_version": "semantic-heuristic-v1",
        }

    def verify_grounding(self, claim: str, evidence_passages: List[str]) -> Dict[str, Any]:
        """Checks whether an agent's claim is grounded in any available evidence passages."""
        if not evidence_passages:
            return {
                "grounding_status": "UNSUPPORTED",
                "confidence": 0.0,
                "best_passage": None,
                "nli_details": {},
            }

        best_score = 0.0
        best_status = "UNSUPPORTED"
        best_passage = None
        best_nli = {}

        for passage in evidence_passages:
            nli_res = self.analyze_claim_vs_evidence(claim=claim, evidence=passage)
            if nli_res["status"] == "CONTRADICTION":
                return {
                    "grounding_status": "CONFLICTING",
                    "confidence": nli_res["confidence"],
                    "best_passage": passage,
                    "nli_details": nli_res,
                }
            elif nli_res["status"] == "ENTAILMENT" and nli_res["confidence"] > best_score:
                best_score = nli_res["confidence"]
                best_status = "SUPPORTED"
                best_passage = passage
                best_nli = nli_res

        if best_status == "SUPPORTED":
            return {
                "grounding_status": "SUPPORTED",
                "confidence": best_score,
                "best_passage": best_passage,
                "nli_details": best_nli,
            }

        return {
            "grounding_status": "UNSUPPORTED",
            "confidence": 0.4,
            "best_passage": evidence_passages[0] if evidence_passages else None,
            "nli_details": {"status": "NEUTRAL", "confidence": 0.5},
        }
