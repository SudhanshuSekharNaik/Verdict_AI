import re
from typing import Any, Dict, List, Optional
from datetime import datetime

from ml import get_ml_registry


class CaseIntakeAgent:
    """Intake Agent: Parses natural language legal narratives into structured case models."""

    def __init__(self):
        self.ml = get_ml_registry()

    def parse_narrative(self, narrative: str, jurisdiction_hint: Optional[str] = None) -> Dict[str, Any]:
        if not narrative or not narrative.strip():
            raise ValueError("Narrative text cannot be empty")

        clean_text = narrative.strip()
        
        # 1. Classify Case Type
        classifier = self.ml.get_classifier()
        case_classification = classifier.classify_case(clean_text)
        case_type = case_classification["label"]

        # 2. Extract Entities using Legal NER
        ner = self.ml.get_ner()
        entities = ner.extract_entities(clean_text[:2000])

        persons = [e["word"] for e in entities if e.get("entity_group") == "PER" or e.get("entity") in ["B-PER", "I-PER"]]
        orgs = [e["word"] for e in entities if e.get("entity_group") == "ORG" or e.get("entity") in ["B-ORG", "I-ORG"]]
        locations = [e["word"] for e in entities if e.get("entity_group") == "LOC" or e.get("entity") in ["B-LOC", "I-LOC"]]

        # 3. Extract Monetary Amounts using Regex
        amount_patterns = [
            r"(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d+)?)",
            r"([\d,]+(?:\.\d+)?)\s*(?:rupees|inr)",
            r"(?:deposit|amount|salary|paid|deducted|withheld|refund)\s*of\s*(?:₹|Rs\.?)?\s*([\d,]+)",
        ]
        amounts = []
        for pattern in amount_patterns:
            matches = re.findall(pattern, clean_text, re.IGNORECASE)
            for m in matches:
                try:
                    val = float(m.replace(",", ""))
                    amounts.append(val)
                except ValueError:
                    pass
        
        disputed_amount = max(amounts) if amounts else None

        # 4. Infer Parties
        plaintiff_name = persons[0] if len(persons) > 0 else "Complainant"
        defendant_name = persons[1] if len(persons) > 1 else (orgs[0] if orgs else "Respondent")

        # 5. Extract Dates & Chronological Events
        date_patterns = [
            r"\b(?:\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4})\b",
            r"\b\d{4}-\d{2}-\d{2}\b",
            r"\b\d{1,2}/\d{1,2}/\d{4}\b",
        ]
        extracted_dates = []
        for pattern in date_patterns:
            extracted_dates.extend(re.findall(pattern, clean_text, re.IGNORECASE))

        # Sentence segmentation
        sentences = [s.strip() for s in re.split(r"[.\n]+", clean_text) if len(s.strip()) > 10]
        
        claims = []
        counterclaims = []
        events = []
        disputed_facts = []
        undisputed_facts = []

        for i, s in enumerate(sentences):
            lower_s = s.lower()
            # Timeline event detection
            found_date = None
            for d in extracted_dates:
                if d.lower() in lower_s:
                    found_date = d
                    break
            
            if found_date:
                events.append({
                    "date_raw_str": found_date,
                    "title": f"Key Milestone: {s[:50]}...",
                    "description": s,
                    "party": "UNDISPUTED" if i == 0 else "PLAINTIFF",
                })

            # Claim vs Defence separation
            if any(k in lower_s for k in ["claim", "seeking", "refund", "unpaid", "demanding", "vacated", "paid", "entitled"]):
                claims.append({
                    "party": "PLAINTIFF",
                    "claim_type": "RESTITUTION" if "refund" in lower_s or "deposit" in lower_s else "BREACH_OF_CONTRACT",
                    "statement": s,
                    "amount": disputed_amount,
                })
                disputed_facts.append(s)
            elif any(k in lower_s for k in ["deducted", "damage", "misconduct", "refused", "defective", "counter", "denies"]):
                counterclaims.append({
                    "party": "DEFENDANT",
                    "claim_type": "DEFENCE_OFFSET",
                    "statement": s,
                    "amount": min(amounts) if len(amounts) > 1 else None,
                })
                disputed_facts.append(s)
            else:
                undisputed_facts.append(s)

        # Build Jurisdiction
        if jurisdiction_hint:
            jurisdiction = f"{jurisdiction_hint} District Court / Consumer Forum"
        elif locations:
            jurisdiction = f"{locations[0]} Consumer Disputes Redressal Commission"
        else:
            jurisdiction = "State Consumer Disputes Redressal Commission"

        # Construct concise title
        title = f"{case_type.title()} Dispute: {plaintiff_name} vs. {defendant_name}"

        return {
            "title": title,
            "case_type": case_type,
            "jurisdiction": jurisdiction,
            "description": clean_text,
            "plaintiff_name": plaintiff_name,
            "defendant_name": defendant_name,
            "disputed_amount": disputed_amount,
            "claims": claims,
            "counterclaims": counterclaims,
            "events": events,
            "disputed_facts": disputed_facts,
            "undisputed_facts": undisputed_facts,
            "confidence_score": round(case_classification.get("confidence", 0.85), 2),
            "analysis_notes": f"Automated Case Intake: Identified {len(claims)} plaintiff claims, {len(counterclaims)} counter assertions, and {len(events)} chronological milestones.",
        }
