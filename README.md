# VerdictAI

> Nyay Manch · न्याय मंच

**VerdictAI** is an evidence-grounded, multi-agent courtroom simulation platform. Instead of a single LLM producing one response to a legal prompt, it orchestrates distinct AI counsel — Prosecution, Defense, Witnesses, and a Presiding Judge — through a turn-by-turn adversarial hearing that is strictly grounded in a canonical fact record and Indian statutory law (BNS / BSA / BNSS, with IPC cross-references).

## 🚀 Live Demo

**[https://verdict-ai-hisy.onrender.com/](https://verdict-ai-hisy.onrender.com/)**

This is the deployed production application — a self-contained FastAPI service that serves both the API and the courtroom UI. Open it to run a full simulated hearing, watch agents argue turn-by-turn, and see an AI Judge deliver a reasoned verdict.

## Problem

Legal reasoning is adversarial and multi-sided, not a single answer. A useful courtroom simulation needs to:

- represent opposing parties who argue *from the same fact record* without inventing evidence
- let evidence, witness testimony, and objections shape what happens next
- preserve state across many turns rather than answering everything in one shot
- apply real statutory provisions (not vague legal-sounding text) to reach a verdict

A single prompt-response LLM call models none of this — there's no adversarial pressure, no persistent case state, and no separation between "arguing a side" and "impartially deciding."

## Solution

VerdictAI models a courtroom as a **stateful, turn-based workflow** rather than one large generation:

- Distinct agents are bound to distinct roles (Prosecution, Defense, Witness, Judge) with role-specific system prompts
- Every case has a canonical fact record; agents are instructed to argue only from facts and evidence actually in that record
- A trial advances one turn at a time via an explicit `/trial/step` endpoint, so the frontend can render each turn as it happens instead of blocking on one long request
- A separate Judge agent — not the arguing agents — evaluates the record and issues a structured verdict, citing applicable Indian statutory provisions

## Key Features

### Multi-Agent Courtroom
Prosecution, Defense, Witness, and Judge agents are implemented as separate classes with their own system prompts (`backend/agents/`), each constrained to the case's fact record.

### Fact-Grounding & Contradiction Checking
A dedicated **Critic Agent** reviews generated arguments for unsupported claims (facts not in the record) and self-contradictions across turns before they're accepted into the trial transcript.

### Evidence & Witnesses
Evidence items and sworn witnesses can be attached to a case and are referenced by agents during arguments and objections (`/cases/{id}/evidence`, `/cases/{id}/witnesses`).

### Turn-by-Turn Trial Orchestration
The trial advances step by step through `POST /cases/{id}/trial/step` (aliased as `/trial/next-turn`), rather than one long-running request — the UI updates as each turn resolves.

### Objections & Evidence Introduction
Dedicated endpoints allow raising objections and introducing evidence mid-trial (`/trial/objection`, `/trial/introduce-evidence`).

### Judge Agent & Verdict
The Judge agent evaluates burden of proof, applicable statutory provisions, and any affirmative defenses raised, then returns a structured verdict (guilty/not guilty or a civil disposition) with a written reasoning summary.

### Indian Statutory Law Lookup
A standalone law-search API (`/api/law/search`, `/api/law/provision/{id}`) serves a curated set of Bharatiya Nyaya Sanhita (BNS) and Bharatiya Sakshya Adhiniyam (BSA) provisions, with legacy IPC/Evidence Act cross-references, used to ground the Judge's reasoning.

### Audience Mode
The frontend includes a passive "Audience Mode" viewing flow — enter the courtroom, a countdown, **"Court is now in session,"** then a **Fast-Forward** mode that autonomously steps the trial through to verdict for the viewer to watch.

## Multi-Agent Architecture

| Agent | File | Responsibility |
|---|---|---|
| Prosecution | `agents/prosecution_agent.py` | Presents the prosecution's theory of the case and arguments from the fact record |
| Defense | `agents/defense_agent.py` | Challenges the prosecution's case, raises defenses/exceptions, delivers closing argument |
| Witness | `agents/witness_agent.py` | Answers questions strictly from an assigned role, linked facts, and shown exhibits — refuses to speculate beyond assigned knowledge |
| Critic | `agents/critic_agent.py` | Fact-checks each generated argument for hallucinated claims or contradictions before it enters the record |
| Judge | `agents/judge_agent.py` | Evaluates evidence and arguments, applies burden of proof and statutory provisions, delivers the final structured verdict |

All agents share a common `BaseCourtroomAgent` (`agents/base_agent.py`), which calls the **Groq API** for inference.

## Trial Orchestration

Trial progression is handled by `backend/orchestration/trial_orchestrator.py` and exposed through the `cases` router:

- `POST /cases/{id}/trial/start` — initializes a trial for a case
- `POST /cases/{id}/trial/step` — advances the trial by one turn and returns the next transcript entry
- `POST /cases/{id}/trial/objection` — raises an objection mid-trial
- `POST /cases/{id}/trial/introduce-evidence` — introduces a new evidence item mid-trial
- `POST /cases/{id}/trial/reset` — resets a trial back to its starting state
- `POST /cases/{id}/run` — runs the case's full pipeline end-to-end in one call

Case, transcript, evidence, and witness state are persisted per case (see **Evidence & Legal Intelligence** below), so a trial can be stepped through incrementally across multiple requests rather than depending on one long-lived connection.

## Evidence & Legal Intelligence

Evidence is submitted per case via `POST /cases/{id}/evidence` and stored alongside the case record. During arguments, agents receive the relevant evidence and witness statements as part of their grounding context, and are constrained to reference only what's actually in that record.

For statutory grounding, `backend/services/rag_service.py` implements a lightweight, self-contained retrieval layer: it builds deterministic hash-based text vectors (no external embedding model) over a local statutory knowledge base and ranks provisions by cosine similarity to a query. It is not a Hugging Face / sentence-transformers pipeline, and does not use BM25 or a cross-encoder reranker.

## Judicial Reasoning

The Judge agent's verdict process (`agents/judge_agent.py`) evaluates:

- the established facts and evidentiary record
- prosecution and defense arguments raised during the trial
- burden of proof (e.g., BSA §104 / prior Evidence Act §101 for the prosecution; BSA §108 / §105 where the accused raises an affirmative defense)
- applicable statutory provisions (BNS with legacy IPC cross-references) relevant to the charge or dispute
- any affirmative defenses (e.g., grave and sudden provocation) evaluated against their specific legal elements

It returns a structured verdict object with a verdict category, applicable statute citations, and a multi-paragraph written reasoning summary.

> **Note:** VerdictAI is an experimental AI simulation. Its outputs are not legal advice and are not a substitute for a real judicial decision.

## Case Library

The application ships with one built-in demo case, seeded automatically on first run: **State of Maharashtra v. Rohan Verma**, a criminal case (murder charge, with forensic and circumstantial evidence) used as the default courtroom scenario. Additional cases can be created through `POST /cases`.

A separate benchmark script (`backend/test_nanavati_benchmark.py`) runs the Judge agent against the real historical facts of **State of Maharashtra v. K.M. Nanavati** (1959 / AIR 1962 SC 605) as a reasoning benchmark. This is a historical case used to sanity-check the Judge's reasoning against a well-documented real judgment — VerdictAI's output on it is an AI simulation, not a reproduction of the actual Supreme Court decision.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python), Uvicorn |
| Frontend | Single static HTML/CSS/vanilla JS page (`frontend/index.html`), served directly by FastAPI's `StaticFiles` |
| Database | SQLite (file-based; `courtroom.db` locally, `/tmp` on Render) |
| LLM Inference | Groq API only — no local model weights, no PyTorch/Transformers at runtime |
| Deployment | Render (Python web service) |

## AI Stack

| Component | Detail |
|---|---|
| LLM Provider | [Groq](https://console.groq.com/) — configured via `GROQ_API_KEY` |
| Default Model | `openai/gpt-oss-120b` (configurable via `GROQ_MODEL`) |
| Agent Orchestration | Custom Python orchestrator (`backend/orchestration/trial_orchestrator.py`) — not LangGraph |
| Statutory Retrieval | Custom deterministic hashed-vector similarity search over a local BNS/BSA knowledge base — no external embedding or reranker models |

## Project Structure

```text
Verdict_AI/
├── frontend/
│   └── index.html          # Self-contained courtroom UI, served as a static file
├── backend/
│   ├── main.py              # FastAPI app entrypoint; mounts frontend + API routers
│   ├── config.py            # Reads GROQ_API_KEY / GROQ_MODEL / ARGUMENT_ROUNDS
│   ├── agents/               # ProsecutionAgent, DefenseAgent, WitnessAgent, CriticAgent, JudgeAgent
│   ├── orchestration/         # trial_orchestrator.py — steps a trial forward turn by turn
│   ├── routers/               # cases.py, law.py — the FastAPI API surface
│   ├── services/              # database.py (SQLite), rag_service.py, law_service.py
│   ├── models/                # Pydantic schemas
│   ├── test_nanavati_benchmark.py
│   └── requirements.txt       # Lean, pinned production dependency set
├── render.yaml
├── .env.example
└── README.md
```

> Note: this repository also contains an earlier scaffold (top-level `agents/`, `rag/`, `ml/`, `courtroom/`, `cases/`, `docs/`, and a Next.js app under `frontend/app`) from a previous iteration of the project. **None of these are used by the deployed application** — the live service runs `backend/main.py`, which serves `frontend/index.html` directly. They're left in the repo but are not part of the current architecture described here.

## API

Once running, interactive OpenAPI docs are available at `/docs`.

Key endpoints (all also available under an `/api` prefix):

```text
GET  /api/health
GET  /cases                              List cases
POST /cases                              Create a case
GET  /cases/demo                         Fetch the built-in demo case
GET  /cases/{case_id}                    Fetch a case
POST /cases/{case_id}/evidence           Add an evidence item
POST /cases/{case_id}/witnesses          Add a witness
POST /cases/{case_id}/trial/start        Start a trial
POST /cases/{case_id}/trial/step         Advance the trial by one turn
POST /cases/{case_id}/trial/objection    Raise an objection
POST /cases/{case_id}/trial/introduce-evidence
POST /cases/{case_id}/trial/reset        Reset a trial
POST /cases/{case_id}/run                Run the full case pipeline
GET  /cases/{case_id}/report             Get the case report
GET  /cases/{case_id}/legal-analysis
GET  /api/law/search                     Search BNS/BSA/BNSS provisions
GET  /api/law/provision/{provision_id}
```

## Local Development

### 1. Clone

```bash
git clone https://github.com/SudhanshuSekharNaik/Verdict_AI.git
cd Verdict_AI
```

### 2. Configure environment

Only two variables are actually required by the running backend (`backend/config.py`):

```bash
cp .env.example backend/.env
```

Then set, at minimum:

```text
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=openai/gpt-oss-120b   # optional, this is the default
```

Get a key at [console.groq.com/keys](https://console.groq.com/keys). (`.env.example` at the repo root also lists variables from the earlier scaffold — such as Postgres/Redis/JWT settings — that the current backend does not read.)

### 3. Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Start the backend

```bash
uvicorn main:app --app-dir backend --reload
```

### 5. Open the app

```text
http://localhost:8000
```

The frontend is served at the root path by the same FastAPI process; there is no separate frontend server to run.

## Environment Variables

| Variable | Purpose | Required |
|---|---|---|
| `GROQ_API_KEY` | Authenticates requests to the Groq API for all agent inference | Yes |
| `GROQ_MODEL` | Groq model ID used for agent inference | No (defaults to `openai/gpt-oss-120b`) |
| `ARGUMENT_ROUNDS` | Number of argument rounds per side in a trial | No (defaults to `2`) |

## Deployment

The production app is deployed on **Render** as a single Python web service, defined in `render.yaml`:

```text
Local:       http://localhost:8000
Production:  Render-provided $PORT (never hardcoded)
```

```text
buildCommand: pip install --no-cache-dir -r backend/requirements.txt
startCommand: uvicorn main:app --app-dir backend --host 0.0.0.0 --port $PORT
healthCheckPath: /api/health
```

`DATABASE_URL` on Render points at a SQLite file under `/tmp` (ephemeral storage — see Limitations). `GROQ_API_KEY` and a generated `SECRET_KEY` are configured as Render environment variables.

## Production Considerations

- **Pinned, lean dependencies** — `backend/requirements.txt` intentionally excludes PyTorch/Transformers so builds stay fast and CPU-only; all model inference happens via the Groq API.
- **Dynamic `$PORT`** — the app never hardcodes a port in production, per Render's requirements.
- **Health endpoint** — `GET /api/health` is used by Render for health checks.
- **Static frontend mount** — the frontend is served directly by FastAPI's `StaticFiles`, avoiding a separate frontend deployment/build step in production.

## Design Philosophy

VerdictAI is not intended to be a single LLM prompt that generates a fictional verdict. It's built around an explicit courtroom workflow:

```text
Case & Fact Record
    ↓
Evidence & Witnesses
    ↓
Prosecution Argument  ⇄  Defense Argument
    ↓
Objections / Critic fact-check
    ↓
Judge: burden of proof, statute, evaluation
    ↓
Verdict
```

## Limitations

- AI-generated arguments and verdicts can contain errors or incomplete legal reasoning.
- The statutory knowledge base and retrieval layer are curated/self-built, not a comprehensive legal database.
- Outputs are simulations for educational/demonstration purposes, not legal advice.
- Render's free-tier deployment uses SQLite on ephemeral disk (`/tmp`); case data does not persist across deploys or restarts.
- LLM responses can vary between runs.

## Roadmap

- Broader statutory knowledge base coverage
- Persistent, non-ephemeral storage for production
- Multi-user / multi-session support
- Expanded case library beyond the current demo case
- Stronger evaluation benchmarks beyond the single Nanavati comparison

## Security & Privacy

- Never commit `.env` or real API keys — use `.env.example` as a template only.
- Rotate any credentials that are ever accidentally exposed.
- No authentication/authorization layer is currently implemented — treat any deployed instance accordingly.

## Disclaimer

VerdictAI is an experimental AI-powered courtroom simulation and legal intelligence project intended for educational, research, and demonstration purposes. AI-generated outputs may be inaccurate or incomplete and should not be treated as legal advice, legal representation, or a real judicial decision.

## License

Private — All rights reserved.

## Author

**Sudhanshu Sekhar Naik**

- GitHub: [github.com/SudhanshuSekharNaik](https://github.com/SudhanshuSekharNaik)
- Project: [github.com/SudhanshuSekharNaik/Verdict_AI](https://github.com/SudhanshuSekharNaik/Verdict_AI)
- Live Demo: [verdict-ai-hisy.onrender.com](https://verdict-ai-hisy.onrender.com/)
