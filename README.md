# ARIA — Account Research & Intelligence Agent

An agentic CRO Business Development intelligence platform. Given a pharma/biotech sponsor name, ARIA autonomously researches the account, scores fit against CRO capabilities, and generates a personalised BD output — account snapshot, pipeline summary, competitive brief, or outreach email.

---

## What it does

ARIA routes a multi-agent research workflow based on your goal:

| Workflow Step | What it produces | Time |
|---|---|---|
| **Account Snapshot** | Quick exec-ready brief for a BD call | ~30s |
| **Pipeline Summary** | Active trial data + CRO opportunities | ~45s |
| **Competitive Brief** | Landscape analysis + positioning | ~45s |
| **Outreach Email** | RAG-grounded personalised BD email | ~90s |

Each step builds on the previous one — trial data and intelligence gathered in step 1 are cached and reused in steps 2–4, so only the synthesiser reruns.

---

## Architecture

```
[Company Name + Goal]
        │
        ▼
┌─────────────────┐
│    Planner      │  ← Analyses goal, routes to correct agents + output format
└────────┬────────┘
         │
    ┌────┴─────────────────────────────────┐
    ▼                  ▼                   ▼
┌─────────┐    ┌─────────────┐    ┌──────────────┐
│  Trial  │    │    Intel    │    │  Fit Scorer  │
│  Agent  │    │    Agent    │    │ (5 weighted  │
│ (CT.gov)│    │ (LLM-only)  │    │  dimensions) │
└────┬────┘    └──────┬──────┘    └──────┬───────┘
     │                │                  │
     └────────┬───────┘                  │
              ▼                          │
     ┌────────────────┐                  │
     │   RAG Layer    │◄─────────────────┘
     │ (50 proposals, │
     │  ChromaDB)     │
     └───────┬────────┘
             ▼
     ┌───────────────┐
     │  Synthesiser  │  ← Produces goal-specific output (email/brief/snapshot)
     └───────────────┘
```

**Data sources (all public, no proprietary data required):**
- [ClinicalTrials.gov v2 API](https://clinicaltrials.gov/data-api/api) — active trials per sponsor
- [SEC EDGAR](https://efts.sec.gov/LATEST/search-index) — 10-K/10-Q filings, R&D signals
- Synthetic CRO proposal corpus (50 docs, 8 therapeutic areas) — RAG knowledge base

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18 + Vite, Tailwind CSS |
| **Backend** | FastAPI + Uvicorn |
| **Agent orchestration** | LangGraph (StateGraph) |
| **LLM** | Anthropic Claude (Haiku by default, configurable) |
| **Embeddings** | OpenAI `text-embedding-3-small` |
| **Vector store** | ChromaDB (persistent, local) |
| **Auth** | JWT, multi-tenant orgs |
| **Database** | SQLite (sessions, usage metering) |

---

## Project Structure

```
aria/
├── backend/
│   ├── agents/           # LangGraph nodes
│   │   ├── planner.py        # Goal analysis + workflow routing
│   │   ├── trial_agent.py    # ClinicalTrials.gov data fetch
│   │   ├── intel_agent.py    # LLM market intelligence
│   │   ├── fit_scorer.py     # 5-dimension CRO fit scoring
│   │   ├── synthesizer.py    # Goal-driven output generation
│   │   └── graph.py          # StateGraph definition
│   ├── auth/             # JWT auth
│   ├── db/               # SQLite session + usage DB
│   ├── middleware/        # Rate limiting
│   ├── models/           # Pydantic schemas
│   ├── rag/              # RAG layer
│   │   ├── corpus.py         # 50 synthetic CRO proposals
│   │   ├── ingest.py         # Build ChromaDB index
│   │   ├── retrieval.py      # Similarity search
│   │   └── evaluate.py       # RAGAS evaluation harness
│   ├── routers/          # FastAPI route handlers
│   │   ├── auth_router.py
│   │   ├── brief.py
│   │   ├── research.py
│   │   └── chat.py
│   └── services/
│       ├── brief_generator.py
│       ├── chat_orchestrator.py
│       ├── clinical_trials.py
│       └── sec_edgar.py
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── api/client.js
│       └── components/
│           ├── SearchForm.jsx
│           ├── ResearchDisplay.jsx
│           ├── BriefDisplay.jsx
│           ├── ChatWindow.jsx
│           ├── SessionSidebar.jsx
│           └── CostDashboard.jsx
├── .env.example
└── ARIA_capstone_reference.md
```

---

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Anthropic API key
- OpenAI API key (for RAG embeddings)

### 1. Clone and install

```bash
git clone https://github.com/Kaushal21394/aria.git
cd aria

# Backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt

# Frontend
cd frontend && npm install && cd ..
```

### 2. Environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Required
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Optional — defaults shown
ARIA_MODEL=claude-haiku-4-5-20251001   # override with claude-sonnet-4-6 for better quality
JWT_SECRET=change-this-in-production   # any string ≥32 chars
```

### 3. Build the RAG index

Only needed once (or after editing `corpus.py`):

```bash
python -m backend.rag.ingest
```

### 4. Run

```bash
# Terminal 1 — Backend (port 8000)
.venv/bin/uvicorn backend.main:app --reload

# Terminal 2 — Frontend (port 5173)
cd frontend && npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

---

## Model configuration

The default model is `claude-haiku-4-5-20251001` — fast and cheap for development. Switch to Sonnet for higher quality output:

```env
ARIA_MODEL=claude-sonnet-4-6
```

All agents read from `settings.aria_model` so changing one env var affects the entire pipeline.

---

## RAG evaluation

Run the RAGAS harness against the 20-question eval set:

```bash
pip install ragas
python -m backend.rag.evaluate
```

Target: faithfulness ≥ 0.7, answer_relevancy ≥ 0.7, context_precision ≥ 0.7.

---

## Roadmap

- [x] Phase 1 — Sponsor brief generator (ClinicalTrials.gov + SEC EDGAR + SSE streaming)
- [x] Phase 2 — Multi-agent research graph (LangGraph, planner-routed, context-preserving)
- [x] Phase 3 — RAG knowledge layer (ChromaDB, OpenAI embeddings, proposal corpus)
- [ ] Phase 4 — Wire chat interface into main UI (`ChatWindow` + `SessionSidebar` built, not yet rendered)
- [ ] Enable web search in Intel Agent (disabled pending higher API rate limits)
- [ ] RAGAS evaluation run
- [ ] MCP end-to-end test (Gmail draft + Google Calendar invite)
