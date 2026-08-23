# ⚖️ AADALAT AI — REST API Reference

Base Endpoint: `/api/v1`

---

## 1. Standard Response Envelope

All API endpoints return a standardized JSON envelope:

### Success Response (HTTP 200/201)
```json
{
  "success": true,
  "data": {
    "id": "c1f7a0c0-2b1b-4f9e-9d22-83b3e8c0e271",
    "case_number": "AAD-2026-X89K",
    "status": "DRAFT"
  },
  "error": null,
  "request_id": "9ba319bc-9e4a-4ca1-abf1-5f8c8fff3b88"
}
```

### Error Response (HTTP 4xx / 5xx)
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ENTITY_NOT_FOUND",
    "message": "Case with ID c1f7a0c0-2b1b-4f9e-9d22-83b3e8c0e271 was not found"
  },
  "request_id": "9ba319bc-9e4a-4ca1-abf1-5f8c8fff3b88"
}
```

---

## 2. Core Endpoints

### 2.1 System & Health
- `GET /health`: Health status of API and subcomponents
- `GET /api/version`: System version and enabled ML/Agent capabilities

### 2.2 Authentication & Users (`/api/v1/auth`)
- `POST /auth/register`: Create user account (`USER`, `JUDGE`, `ADMIN`)
- `POST /auth/login`: Authenticate and obtain JWT Bearer token
- `GET /auth/me`: Get current authenticated profile and permissions

### 2.3 Case Management (`/api/v1/cases`)
- `POST /cases`: Create new legal case
- `GET /cases`: List cases (with pagination, status, and search filters)
- `GET /cases/{id}`: Retrieve detailed case record
- `PATCH /cases/{id}`: Update case parameters or status
- `DELETE /cases/{id}`: Soft delete or purge case
- `POST /cases/intake`: Natural language case intake parser (extracts parties, claims, amounts, dates)
- `GET /cases/{id}/similar`: Retrieve semantically similar historical/precedent cases

### 2.4 Evidence Vault & Intelligence (`/api/v1/evidence`)
- `POST /cases/{id}/evidence`: Upload document (PDF, PNG, JPG, TXT, DOCX)
- `GET /cases/{id}/evidence`: List all evidence admitted/cataloged for case
- `GET /evidence/{id}`: Detailed view of evidence metadata, OCR text, and chunks
- `GET /cases/{id}/evidence-graph`: Knowledge graph nodes & edges (claims, evidence, parties)
- `GET /cases/{id}/timeline`: Chronological event timeline with conflict detection flags

### 2.5 Hugging Face ML & NLP (`/api/v1/ml`)
- `POST /ml/ner`: Extract legal entities (`PERSON`, `COURT`, `STATUTE`, `SECTION`, etc.)
- `POST /ml/classify/case`: Zero-shot case category classification
- `POST /ml/classify/document`: Document typology classification
- `POST /ml/nli`: Natural Language Inference (Entailment / Contradiction / Neutral)
- `POST /ml/grounding`: Ground AI claim against evidence vector passages

### 2.6 Legal RAG & Research (`/api/v1/research`)
- `POST /research/search`: Hybrid retrieval (BM25 + Dense Vector) across legal knowledge base
- `POST /research/validate-citation`: Verify statutory or precedent citation against corpus
- `POST /research/agent-query`: Query Legal Research Agent for case theory authorities

### 2.7 Court Intelligence (`/api/v1/court`)
- `POST /court/search`: Search official / permitted court judgments and orders
- `POST /court/documents/import`: Ingest public court document into legal corpus
- `POST /court/documents/{id}/analyze`: Structure extraction (Facts, Issues, Reasoning, Order)

### 2.8 Multi-Agent Courtroom (`/api/v1/courtroom`)
- `POST /courtroom/{case_id}/session/start`: Initialize courtroom state machine
- `GET /courtroom/{case_id}/state`: Current courtroom stage, active speaker, rounds
- `POST /courtroom/{case_id}/step`: Advance courtroom turn (Opening, Attack, Rebuttal, Cross-Exam)
- `POST /courtroom/{case_id}/judge/question`: Human Judge asks direct question to Plaintiff or Defence AI
- `POST /courtroom/{case_id}/judge/action`: Judge controls (Pause, Resume, Request Evidence, Flag Issue)
- `POST /courtroom/{case_id}/judgment`: Human Judge submits formal verdict and reasoning
- `GET /courtroom/{case_id}/report`: Comprehensive post-judgment post-mortem report

### 2.9 Evaluation Suite (`/api/v1/evaluation`)
- `GET /evaluation/benchmarks`: List ground truth benchmarks across the 5 demo cases
- `POST /evaluation/run`: Execute automated evaluation suite (NER F1, NLI Accuracy, Retrieval Recall@K, Grounding Rate)
