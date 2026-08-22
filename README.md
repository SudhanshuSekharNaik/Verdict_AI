# Nyay Manch (न्याय मंच) — AI Courtroom Arena & Indian Law Reasoning Platform

[![Tests](https://img.shields.io/badge/Playwright%20E2E-13%20Passing-brightgreen)]()
[![Backend](https://img.shields.io/badge/FastAPI-2.5.0-blue)]()
[![LLM](https://img.shields.io/badge/Groq-Multi--Model%20Fallback-orange)]()
[![Jurisprudence](https://img.shields.io/badge/Statutes-BNS%20%7C%20BNSS%20%7C%20BSA%202023-gold)]()

**Nyay Manch** is an autonomous, turn-based multi-agent courtroom simulator and Indian statutory legal reasoning engine. It models realistic adversarial proceedings under the **Bharatiya Nyaya Sanhita (BNS)**, **Bharatiya Sakshya Adhiniyam (BSA)**, and **Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023**.

---

## 🏛️ Key Features

- **Adversarial AI Courtroom Simulation**: Sequential turns between Prosecution and Defence agents, witness examination under oath, cross-examination, procedural objections, and judicial deliberation.
- **14 Specialist AI Advocates**: Roster of distinct legal personalities across criminal defense, prosecution, constitutional law, cyber forensics, and commercial litigation.
- **8-Step Case Filing Intake Wizard**: Comprehensive dossier builder for facts, charges, counsel mutual-exclusivity, registered exhibits (P-EX / D-EX), witness depositions, and legal issues.
- **Dual Courtroom Modes**:
  - **Audience Mode**: Autonomous broadcast where the user observes the entire trial unfold passively with synchronized audio narration.
  - **Filer Mode**: Interactive litigation with turn advancing, procedural objections, evidence introduction, and instant fast-forwarding to verdict.
- **Official Indian Statutory Library**: Verified semantic search and provision inspector for BNS, BNSS, BSA, IT Act, and the Constitution of India.
- **Cinematic Verdict & Formal Judicial Decree**: Multi-prong judicial reasoning, issue findings, evidentiary citations, and one-click export (Markdown & JSON).
- **High-Throughput Multi-Model Fallback**: Dynamic Groq API quota failover across `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, and `qwen/qwen3.6-27b` with zero rate-limit interruptions.

---

## 🏗️ Architecture

```
                                  ┌────────────────────────┐
                                  │   FastAPI Web Server   │
                                  │   & Static Frontend    │
                                  └───────────┬────────────┘
                                              │
                                  ┌───────────▼────────────┐
                                  │   Trial Orchestrator   │
                                  │   (State Machine)      │
                                  └───────────┬────────────┘
                                              │
        ┌─────────────────────────────────────┼─────────────────────────────────────┐
        │                                     │                                     │
┌───────▼────────┐                   ┌────────▼─────────┐                  ┌────────▼────────┐
│ Prosecution    │                   │ Defense          │                  │ Presiding Judge │
│ Agent (Groq)   │                   │ Agent (Groq)     │                  │ Agent (Groq)    │
└───────┬────────┘                   └────────┬─────────┘                  └────────┬────────┘
        │                                     │                                     │
        └──────────────────┬──────────────────┘                                     │
                           │                                                        │
                  ┌────────▼─────────┐                                              │
                  │ Witness Stand    │◄─────────────────────────────────────────────┘
                  │ (Witness Agents) │          (Admissibility, Rulings & Decree)
                  └────────┬─────────┘
                           │
                  ┌────────▼─────────┐
                  │ Statutory Engine │
                  │ (BNS, BSA, BNSS) │
                  └──────────────────┘
```

---

## 🚀 Quick Start (Local Setup)

### 1. Clone & Configure Environment

```bash
git clone https://github.com/your-username/courtroom-arena.git
cd courtroom-arena/backend

# Create & activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create your .env file
cp .env.example .env
```

Add your free [Groq API Key](https://console.groq.com/keys) to `backend/.env`:
```env
GROQ_API_KEY=gsk_your_actual_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

### 2. Run the Backend API & Frontend

```bash
# Start FastAPI backend (serves API on :8000 and static frontend on /)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

*(Optional standalone frontend dev server: `python -m http.server 5500` from the root directory).*

---

## 🧪 Automated Testing Suite

The codebase includes full Playwright end-to-end and exploratory test suites:

```bash
# Run all automated tests
pytest tests -v
```

---

## 🌐 Production Deployment

### Option 1: Docker / Container
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
WORKDIR /app/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Option 2: Render / Railway / Heroku
- **Build Command**: `pip install -r backend/requirements.txt`
- **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**: Set `GROQ_API_KEY` in your platform dashboard.

---

## 📜 Disclaimer
Nyay Manch is an educational, research, and simulation platform. It does not provide legal advice and does not represent actual judicial proceedings or binding judgments.
