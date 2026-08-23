import re
from typing import Any, Dict, List, Optional


class LegalNER:
    """Legal Named Entity Recognition using Hugging Face Transformers with heuristic fallback."""

    def __init__(self, model_name: str = "dslim/bert-base-NER"):
        self.model_name = model_name
        self.nlp = None
        self._initialized = False

    def _lazy_init(self):
        if not self._initialized:
            try:
                from transformers import pipeline
                self.nlp = pipeline("ner", model=self.model_name, aggregation_strategy="simple")
            except Exception as e:
                self.nlp = None
            self._initialized = True

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        if not text or not text.strip():
            return []

        self._lazy_init()
        entities: List[Dict[str, Any]] = []

        if self.nlp:
            try:
                max_chars = 1500
                chunks = [text[i : i + max_chars] for i in range(0, len(text), max_chars)]
                for chunk in chunks:
                    res = self.nlp(chunk)
                    for item in res:
                        entities.append({
                            "entity_group": item.get("entity_group", "MISC"),
                            "word": item.get("word", ""),
                            "score": float(item.get("score", 0.9)),
                            "start": item.get("start", 0),
                            "end": item.get("end", 0),
                        })
            except Exception:
                pass

        # Robust Legal Heuristic Entity Extractor (Guarantees legal tokens: STATUTE, SECTION, COURT, MONEY, DATE)
        # 1. Statutes & Sections
        statute_matches = re.finditer(r"(?:Section|Sec\.?|Article|Art\.?)\s*(\d+[A-Za-z]?(?:\(\d+\))?)\s*(?:of\s*(?:the\s*)?([A-Z][a-zA-Z\s]{3,40}(?:Act|Code|Rules|Constitution)))?", text, re.IGNORECASE)
        for m in statute_matches:
            entities.append({
                "entity_group": "STATUTE",
                "word": m.group(0),
                "section": m.group(1),
                "act": m.group(2) if m.group(2) else "Statute",
                "score": 0.98,
                "start": m.start(),
                "end": m.end(),
            })

        # 2. Courts
        court_matches = re.finditer(r"\b(?:Supreme Court|High Court|District Court|Consumer Disputes Redressal Commission|National Commission|Tribunal|Sessions Court)\b", text, re.IGNORECASE)
        for m in court_matches:
            entities.append({
                "entity_group": "COURT",
                "word": m.group(0),
                "score": 0.95,
                "start": m.start(),
                "end": m.end(),
            })

        # 3. Money
        money_matches = re.finditer(r"(?:₹|Rs\.?|INR)\s*[\d,]+(?:\.\d+)?", text, re.IGNORECASE)
        for m in money_matches:
            entities.append({
                "entity_group": "MONEY",
                "word": m.group(0),
                "score": 0.99,
                "start": m.start(),
                "end": m.end(),
            })

        # 4. Dates
        date_matches = re.finditer(r"\b(?:\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})\b", text, re.IGNORECASE)
        for m in date_matches:
            entities.append({
                "entity_group": "DATE",
                "word": m.group(0),
                "score": 0.97,
                "start": m.start(),
                "end": m.end(),
            })

        return entities
