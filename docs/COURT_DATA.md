# ⚖️ AADALAT AI — Court Intelligence & Permitted Ingestion

## 1. Compliance & Legal Ingestion Guardrails
Aadalat AI adheres strictly to the following principles:
- **No Anti-Bot Bypassing:** We do NOT bypass CAPTCHA, Cloudflare challenges, OTP logins, or anti-scraping protections on private court portals.
- **Permitted Sources Only:** Ingestion connects only to authorized open datasets, public domain judgments, licensed repositories, and user-uploaded trial documents.
- **Clear Provenance:** Every ingested judgment, statute, or order maintains an unalterable provenance record (Source URL, Hash, Retrieval Timestamp, Bench, CNR).

---

## 2. Court Data Ingestion Pipeline

```mermaid
graph TD
    Source["🏛️ Official Open Legal Sources / User Court Uploads"] --> Validator["🛡️ Access & Format Validator"]
    Validator --> Ingestion["📥 Document Ingestion Worker"]
    Ingestion --> HashStore["🔒 SHA-256 Hashing & Storage"]
    
    HashStore --> PyMuPDF["📄 PDF / OCR Structure Extraction"]
    PyMuPDF --> NER_Extract["🏷️ Legal NER & Entity Linking"]
    NER_Extract --> Classifier["📑 Document & Jurisdiction Classifier"]
    
    Classifier --> Structuring["🧩 Court Structure Parser"]
    
    subgraph StructuredFields["Extracted Court Structure"]
        CourtName["Court & Bench"]
        CaseNumber["CNR / Case Number"]
        Judges["Presiding Judge(s)"]
        Facts["Summary of Facts"]
        Issues["Issues Framed"]
        Ratio["Ratio Decidendi"]
        Disposal["Final Order / Disposal"]
    end
    
    Structuring --> StructuredFields
    StructuredFields --> VectorIndex["🗄️ Legal Knowledge Base Indexing"]
```

---

## 3. Supported Court Data Connectors
1. **`UserCourtDocConnector`**: Ingests user-submitted pleadings, certified judgment copies, and case orders.
2. **`PublicCaseArchiveConnector`**: Loads open legal databases and landmark public interest judgments.
3. **`FictionalDemoDataConnector`**: Generates synthetic, fully coherent trial bundles for the 5 benchmark cases.
