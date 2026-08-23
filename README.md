# Aadalat AI

Evidence-grounded multi-agent courtroom simulation and legal intelligence platform.

## Quick Start

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Start with Docker
docker-compose up --build

# 3. Seed demo data
docker-compose exec backend python scripts/seed_database.py

# 4. Open
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

## Architecture

```
Court Intelligence → Hugging Face NLP → Case/Evidence Intelligence → RAG → Plaintiff/Defence Agents → Human Judge
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React 18, Tailwind CSS |
| Backend | FastAPI, SQLAlchemy, PostgreSQL |
| AI/ML | Hugging Face Transformers, Sentence Transformers |
| Agents | LangGraph, 7 specialized agents |
| RAG | Hybrid BM25 + Vector, Cross-Encoder Reranking |
| Knowledge Graph | NetworkX |
| Document AI | PDF parsing, OCR |

### AI Stack

| Component | Model |
|-----------|-------|
| Legal NER | `dslim/bert-base-NER` |
| Case Classification | `facebook/bart-large-mnli` |
| NLI/Contradiction | `roberta-large-mnli` |
| Embeddings | `sentence-transformers/all-MiniLM-L-6-v2` |
| Reranking | `cross-encoder/ms-marco-MiniLM-L-6-v2` |

## API Documentation

Once running, visit `http://localhost:8000/docs` for the full OpenAPI specification.

## Demo Cases

5 pre-loaded demo cases:
1. Security Deposit Dispute (Property)
2. Used Car Defect (Consumer)
3. Wrongful Termination (Employment)
4. Online Product Defect (Consumer)
5. Payment Dispute (Financial)

## License

Private — All rights reserved.
