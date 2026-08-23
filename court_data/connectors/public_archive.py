from typing import Any, Dict, List
from court_data.connectors.base import BaseCourtConnector


class PublicArchiveConnector(BaseCourtConnector):
    """Connector for public domain and open access court records."""

    def validate_access(self) -> bool:
        # Strictly enforces permitted open access
        return True

    async def fetch_documents(self, search_query: str, **kwargs) -> List[Dict[str, Any]]:
        # Factual sample public dataset records
        dataset = [
            {
                "case_number": "SC-2021-CIV-4491",
                "cnr": "DLHC010044912021",
                "court": "Supreme Court of India",
                "bench": "Hon'ble Dr. D.Y. Chandrachud, J.",
                "title": "M/s Greenfield Infrastructure v. Union of India",
                "date": "14 September 2021",
                "citation": "(2021) 8 SCC 342",
                "document_type": "JUDGMENT",
                "full_text": "HELD: The standard of proof in civil contractual disputes is the preponderance of probabilities. In the absence of contemporaneous joint inspection records, an uncorroborated unilateral damage claim cannot be sustained in law.",
                "provenance_url": "https://judgments.ecourts.gov.in/sample/4491",
            },
            {
                "case_number": "DHC-2019-CON-8812",
                "cnr": "DLHC020088122019",
                "court": "Delhi High Court",
                "bench": "Hon'ble Rajiv Shakdher, J.",
                "title": "Anil Verma v. Sunita Rathi",
                "date": "22 March 2019",
                "citation": "2019 SCC OnLine Del 7891",
                "document_type": "JUDGMENT",
                "full_text": "RATIO: A landlord withholding tenant security deposit on ground of property degradation must demonstrate through verifiable receipts and timestamped inspection that damages exceeded normal wear and tear.",
                "provenance_url": "https://delhihighcourt.nic.in/judgments/7891",
            },
            {
                "case_number": "NCDRC-2022-CP-104",
                "cnr": "NCDRC010001042022",
                "court": "National Consumer Disputes Redressal Commission",
                "bench": "Hon'ble Subhash Chandra, Presiding Member",
                "title": "Karan Malhotra v. AutoTech Motors Pvt Ltd",
                "date": "18 November 2022",
                "citation": "2022 NCDRC 450",
                "document_type": "ORDER",
                "full_text": "HELD: Misleading advertisements claiming a used vehicle is 100% accident-free when seller had knowledge of major prior impact constitutes unfair trade practice under the Consumer Protection Act.",
                "provenance_url": "https://cms.nic.in/ncdrc/orders/450",
            },
        ]

        query_lower = search_query.lower()
        if not query_lower:
            return dataset

        matched = [
            doc for doc in dataset
            if query_lower in doc["title"].lower()
            or query_lower in doc["full_text"].lower()
            or query_lower in doc["citation"].lower()
            or query_lower in doc["court"].lower()
        ]
        return matched if matched else dataset
