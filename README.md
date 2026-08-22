# Nyay Manch (न्याय मंच)
### AI Courtroom Arena & Indian Statutory Legal Reasoning Platform

<p align="center">
  <em>An autonomous, multi-agent adversarial courtroom simulator grounded in Indian law.</em>
</p>

<p align="center">
  <a href="https://nyay-manch.onrender.com"><img alt="Live Demo" src="https://img.shields.io/badge/Live%20Demo-nyay--manch.onrender.com-success?style=for-the-badge" /></a>
</p>

<p align="center">
  <img alt="Tests" src="https://img.shields.io/badge/Playwright%20E2E-13%20Passing-brightgreen" />
  <img alt="Backend" src="https://img.shields.io/badge/FastAPI-2.5.0-blue" />
  <img alt="LLM" src="https://img.shields.io/badge/Groq-Multi--Model%20Fallback-orange" />
  <img alt="Jurisprudence" src="https://img.shields.io/badge/Statutes-BNS%20%7C%20BNSS%20%7C%20BSA%202023-gold" />
  <img alt="Deployed" src="https://img.shields.io/badge/Deployed-Render-46E3B7" />
  <img alt="License" src="https://img.shields.io/badge/License-MIT-lightgrey" />
</p>

<p align="center">
  <strong><a href="https://nyay-manch.onrender.com">🔴 Live Demo — nyay-manch.onrender.com</a></strong>
</p>

---

> ⚖️ **Educational & Research Simulation.** Nyay Manch does not provide legal advice
> and does not represent actual judicial proceedings or binding judgments. See
> [Disclaimer](#-disclaimer).

## Table of Contents

- [What is Nyay Manch?](#-what-is-nyay-manch)
- [Highlights](#-highlights)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start-local-setup)
- [Project Structure](#-project-structure)
- [Automated Testing](#-automated-testing-suite)
- [Deployment](#-production-deployment)
- [Benchmarking Against Real Case Law](#-benchmarking-against-real-case-law)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)
- [Disclaimer](#-disclaimer)

---

## 🏛️ What is Nyay Manch?

Nyay Manch is a turn-based, multi-agent courtroom simulator built to explore how
LLM agents reason through adversarial legal argument. Rather than a single model
producing a plausible-sounding answer, a full case is contested — a Prosecution
agent and a Defence agent build independent theories from a shared, canonical
fact record, examine witnesses, introduce evidence, and argue before a Presiding
Judge agent that must issue a reasoned, statute-grounded verdict.

The platform models proceedings under India's modernized criminal law framework —
the **Bharatiya Nyaya Sanhita (BNS)**, **Bharatiya Sakshya Adhiniyam (BSA)**, and
**Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023** — alongside a wider library of
practice areas (family, civil, corporate, cyber, IP, tax, constitutional,
employment, environmental, human rights, and banking law).

## 🎯 Highlights

*For anyone skimming before a deeper read:*

- **Multi-agent adversarial architecture** — not a single LLM call, but
  independent Prosecution, Defence, Judge, and Witness agents reasoning from a
  shared, canonically-constrained fact record.
- **RAG-grounded domain expertise** — 14 specialist counsel agents, each
  retrieving from its own per-domain vector index (real statutes, landmark case
  doctrine) rather than reasoning from general pretraining alone.
- **Validated against real jurisprudence** — benchmarked against a landmark,
  publicly-decided Indian Supreme Court case (K.M. Nanavati v. State of
  Maharashtra, 1959); the simulation independently reached the same verdict the
  real courts did. See [Benchmarking](#-benchmarking-against-real-case-law).
- **Production-deployed**, not just a local demo — live on Render with a
  memory-optimized inference pipeline (see [Deployment](#-production-deployment)
  for the specific RAM-cost tradeoff that shaped this).
- **Tested**, not just built — a Playwright E2E regression suite plus an
  agentic exploratory-testing layer for catching UX friction scripted
  assertions miss.

## ✨ Key Features

- **Adversarial AI Courtroom Simulation** — sequential turns between Prosecution
  and Defence, witness examination under oath, cross-examination, procedural
  objections, and judicial deliberation.
- **14 Specialist AI Advocates** — a roster of distinct counsel agents (Criminal
  Defence, Public Prosecutor, Family & Matrimonial, Civil, Real Estate,
  Corporate, Cyber, IP, Tax, Constitutional, Employment, Environmental, Human
  Rights, Banking & Finance), each grounded in a domain-specific knowledge base
  via retrieval-augmented generation — not live web scraping.
- **8-Step Case Filing Intake Wizard** — Case Identity → Counsel Selection →
  Facts → Issues → Parties → Evidence → Witnesses → Review, with a canonical
  fact record every agent is constrained to reason from.
- **Counsel Mutual-Exclusivity** — the filing and opposing sides can never be
  assigned the same specialist agent, enforced on both the frontend and the API.
- **Dual Courtroom Modes**
  - **Audience Mode** — a fully passive, autonomous broadcast. The trial plays
    from opening statement to verdict with no user interaction required or
    permitted; the agents run the case entirely on their own.
  - **Filer Mode** — interactive litigation with manual turn advancement,
    objections, exhibit introduction, and judge rulings, plus a
    fast-forward-to-verdict option.
- **Official Indian Statutory Library** — a searchable provision inspector
  across BNS, BNSS, BSA, the IT Act, and the Constitution of India.
- **Cinematic Verdict & Formal Judicial Decree** — issue-by-issue judicial
  findings, evidentiary citations, statutory provision evaluation, and one-click
  export to Markdown or JSON.
- **High-Throughput Multi-Model Fallback** — dynamic Groq API quota failover
  across multiple models with zero rate-limit interruptions.

## 🏗️ Architecture

```
                                  ┌────────────────────────┐
                                  │   FastAPI Web Server    │
                                  │   & Static Frontend     │
                                  └───────────┬─────────────┘
                                              │
                                  ┌───────────▼─────────────┐
                                  │   Trial Orchestrator     │
                                  │   (State Machine)        │
                                  └───────────┬─────────────┘
                                              │
        ┌─────────────────────────────────────┼─────────────────────────────────────┐
        │                                     │                                     │
┌───────▼────────┐                   ┌────────▼─────────┐                  ┌────────▼────────┐
│ Prosecution    │                   │ Defence           │                  │ Presiding Judge │
│ Agent (Groq)   │                   │ Agent (Groq)      │                  │ Agent (Groq)    │
└───────┬────────┘                   └────────┬─────────┘                  └────────┬────────┘
        │                                     │                                     │
        └──────────────────┬──────────────────┘                                     │
                            │                                                        │
                   ┌────────▼─────────┐                                              │
                   │ Witness Stand     │◄─────────────────────────────────────────────┘
                   │ (Witness Agents)  │          (Admissibility, Rulings & Decree)
                   └────────┬─────────┘
                            │
                   ┌────────▼─────────┐
                   │ RAG Knowledge Base│
                   │ (per-domain index)│
                   └────────┬─────────┘
                            │
                   ┌────────▼─────────┐
                   │ Statutory Engine  │
                   │ (BNS, BSA, BNSS)  │
                   └────────────────────┘
```

Each specialist counsel agent's system prompt is augmented at case-creation
time with passages retrieved from its own domain's vector index — grounding
its arguments in real statutory text and landmark-case doctrine rather than
general-purpose legal knowledge.

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| LLM Inference | Groq API, multi-model fallback |
| Agent Knowledge | RAG — local vector store (FAISS/ChromaDB) per legal domain |
| Frontend | HTML / CSS / JS (single-file, no build step) |
| Testing | Playwright (E2E), agentic exploratory testing |
| Deployment | Render (Python 3 web service) |
| Statutes Modeled | BNS, BNSS, BSA (2023), IT Act 2000, Constitution of India, and 10+ other Indian acts by practice area |

## 🚀 Quick Start (Local Setup)

### 1. Clone & Configure Environment

```bash
git clone https://github.com/SudhanshuSekharNaik/Nyay_Manch.git
cd Nyay_Manch/backend

# Create & activate a virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create your .env file
cp .env.example .env
```

Add your free [Groq API key](https://console.groq.com/keys) to `backend/.env`:

```env
GROQ_API_KEY=gsk_your_actual_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

### 2. Run the Backend & Frontend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

*(Optional standalone frontend dev server: `python -m http.server 5500` from
the repository root.)*

## 📁 Project Structure

```
Nyay_Manch/
├── backend/
│   ├── main.py                      FastAPI app entrypoint
│   ├── config.py                    Env var loading, model fallback config
│   ├── requirements.txt
│   ├── .env.example
│   ├── models/                      Pydantic schemas (Case, Verdict, etc.)
│   ├── agents/                      Prosecution, Defence, Judge, Witness agents
│   ├── knowledge_base/              Per-domain statute/case-law source files
│   ├── rag/                         Chunking, embedding, retrieval pipeline
│   ├── orchestration/               Trial state machine
│   ├── services/                    Case store, transcript rendering
│   └── routers/                     API endpoints
├── frontend/
│   └── index.html                   Single-file UI (docket/ledger design system)
└── tests/
    ├── e2e/                         Playwright regression suite
    └── exploratory/                 Agentic UX exploration scripts
```

## 🧪 Automated Testing Suite

The codebase includes a Playwright end-to-end suite covering demo login, the
full 8-step case-filing flow, counsel mutual-exclusivity, both courtroom modes,
verdict export, and landing-page CTA hygiene — plus a supplementary agentic
exploratory testing layer for catching UX friction that scripted assertions
wouldn't think to check.

```bash
# Run the full E2E suite
pytest tests/e2e -v

# Run exploratory agentic checks (slower, qualitative)
python tests/exploratory/agentic_checks.py
```

## 🌐 Production Deployment

**Live at [nyay-manch.onrender.com](https://nyay-manch.onrender.com)**, deployed
as a Render Python 3 web service.

### Deployment notes

A real engineering tradeoff worth documenting: the initial argument-classifier
implementation used a local HuggingFace zero-shot model
(`facebook/bart-large-mnli`), which alone consumes ~1.6GB of RAM — enough to
force a $25-85/month Render instance just to hold model weights in memory. This
was refactored to a lightweight Groq prompt-based classification call instead,
reusing the same LLM already powering the courtroom agents. This cut the
memory footprint enough to run comfortably on Render's Starter tier, with no
loss of classification quality.

### Option 1 — Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
WORKDIR /app/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Option 2 — Render / Railway / Heroku

- **Root Directory:** `backend`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables:** set `GROQ_API_KEY` in your platform's dashboard.

## ⚖️ Benchmarking Against Real Case Law

To validate the judge agent's reasoning quality, this project was benchmarked
against **K.M. Nanavati v. State of Maharashtra (1959)** — a landmark, fully
public Indian Supreme Court case with a well-documented real-world outcome.
The simulation reached the same verdict as the actual courts (guilty of
murder under IPC §302, provocation defense rejected), and the exercise
surfaced a concrete, fixable gap between a *correct verdict* and *correct
legal reasoning* — the judge agent's issue-by-issue analysis has since been
strengthened to require it to engage with every framed legal issue
individually rather than reaching a verdict that merely happens to be
consistent with them.

## 🗺️ Roadmap

- [ ] Populate RAG knowledge bases for all 14 legal specialties (currently
      prioritized: Criminal, Family, Civil)
- [ ] Persist cases in Postgres instead of the in-memory store
- [ ] Expand the statutory library's semantic search coverage
- [ ] Additional real-case benchmarks across other practice areas

## 🤝 Contributing

Issues and pull requests are welcome. Please open an issue describing the
change before submitting a large PR, so we can align on direction first.

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.

## 📜 Disclaimer

Nyay Manch is an educational, research, and simulation platform. It does not
provide legal advice, does not represent actual judicial proceedings, and its
outputs are not binding judgments. Statutory references are provided for
educational purposes and should be independently verified — via
[India Code](https://www.indiacode.nic.in) or a qualified legal professional —
before being relied upon for any real matter.
