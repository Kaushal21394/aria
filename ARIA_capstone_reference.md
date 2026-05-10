# ARIA — Account Research & Intelligence Agent
## Capstone Project Reference · AI Engineering Roadmap

---

## Project Overview

**ARIA** is an end-to-end agentic system for the Commercial side of a CRO business. Given a pharma/biotech sponsor's company name, ARIA autonomously researches the account, scores its fit against CRO capabilities, and generates a personalised BD outreach package — brief, email draft, and calendar invite.

**Why this project:** Covers every foundational AI engineering skill across 4 phases. Each phase produces a standalone Plugin that is independently useful and incrementally adds to the full system. No proprietary data required.

**Domain:** CRO Commercial / Business Development (Sales, BD leads, sponsor research)

**Total timeline:** ~9 months (Phases 1–4 run sequentially, each ~2 months)

---

## System Architecture Summary

```
[Trigger: Company Name Input]
           │
           ▼
┌─────────────────────────────────┐
│  Plugin 1 — Sponsor Brief Gen  │  ← ClinicalTrials.gov API, SEC EDGAR, web
│  Phase 1 · Anthropic SDK        │
└─────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────┐
│  Plugin 2 — Multi-Agent Orchestrator                    │  ← Web search MCP
│  Phase 2 · LangGraph · MCP tool use · ReAct            │
│  [Trial Agent] [Intel Agent] [Fit Scorer] [Outreach]   │
└─────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  Plugin 3 — RAG Knowledge Layer │  ← Pinecone/pgvector, proposals corpus
│  Phase 3 · Embeddings · RAGAS  │
└─────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  Plugin 4 — Production SaaS    │  ← Gmail MCP, Google Calendar MCP
│  Phase 4 · FastAPI · Streamlit │
└─────────────────────────────────┘
           │
           ▼
[BD Brief PDF] [Email Draft] [Calendar Invite] [Fit Score 0–100]
```

---

## Data Sources (No Proprietary Data Required)

| Source | What it provides | Access |
|---|---|---|
| ClinicalTrials.gov REST API | Active/historical trials per sponsor, phases, endpoints, sites | Free, no auth |
| SEC EDGAR | 10-K/10-Q filings — therapeutic focus, R&D spend, pipeline | Free, no auth |
| Web search (MCP) | Press releases, pipeline news, partnerships | Via MCP tool |
| Synthetic CRM | Past BD interactions, notes (Claude-generated) | Self-generated |
| Synthetic proposals | Past proposal summaries for RAG corpus (50 docs) | Self-generated with Claude |

---

## MCP Integrations

| MCP | Plugin | Purpose |
|---|---|---|
| Web search | Plugin 2 — Intel Agent | Sponsor news, pipeline updates |
| Gmail MCP | Plugin 4 | Stage outreach email drafts in Gmail |
| Google Calendar MCP | Plugin 4 | Create follow-up meeting slots |

> **Note:** Gmail and Google Calendar MCPs are already connected in your Claude account. Web search MCP is available as a tool in the Anthropic API (`web_search_20250305`).

---

## Plugin 1 — Sponsor Brief Generator

**Phase:** 1 (Months 1–2)
**Status when complete:** Standalone useful tool

### What You Build
A Python function (later a FastAPI endpoint) that accepts a pharma/biotech company name and returns a structured intelligence brief as markdown/JSON.

### Inputs
- `company_name: str` — e.g. `"Novo Nordisk"`, `"AstraZeneca"`
- `config: dict` — optional filters (therapeutic area, trial phase, geography)

### Outputs
A structured brief containing:
- Company overview (size, HQ, therapeutic focus)
- Active clinical trials (count, phases, TAs, geographic spread)
- Recent pipeline milestones (last 12 months)
- R&D investment signals from SEC filings
- Historical CRO partnership indicators
- Key contacts (if available via public sources)

### Core Technical Components

```python
# Stack
anthropic          # Anthropic Python SDK
httpx              # Async HTTP for ClinicalTrials.gov + EDGAR APIs
pydantic           # Structured output validation
fastapi            # API wrapper (end of Phase 1)
streamlit          # Simple UI for testing
python-dotenv      # Config management
```

### Key API Calls

```python
# ClinicalTrials.gov v2 API
GET https://clinicaltrials.gov/api/v2/studies
  ?query.spons={company_name}
  &filter.overallStatus=RECRUITING,ACTIVE_NOT_RECRUITING
  &fields=NCTId,BriefTitle,Phase,Condition,LeadSponsorName,StartDate
  &pageSize=50

# SEC EDGAR full-text search
GET https://efts.sec.gov/LATEST/search-index?q="{company_name}"&dateRange=custom&startdt=2024-01-01&forms=10-K
```

### Anthropic SDK Pattern

```python
import anthropic

client = anthropic.Anthropic()

def generate_sponsor_brief(company_name: str, raw_data: dict) -> str:
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        system="""You are a CRO business development analyst. 
        Given structured data about a pharma sponsor, produce a concise 
        intelligence brief in the specified JSON schema.""",
        messages=[{
            "role": "user",
            "content": f"""
            Company: {company_name}
            Clinical trials data: {raw_data['trials']}
            SEC filing excerpts: {raw_data['sec_data']}
            
            Generate a BD intelligence brief following the schema:
            {{
              "company_overview": "...",
              "pipeline_summary": [...],
              "trial_activity": {{...}},
              "opportunity_signals": [...],
              "recommended_service_areas": [...]
            }}
            """
        }]
    )
    return response.content[0].text
```

### AI Skills Learned (Phase 1)
- LLM API fundamentals (model selection, token budgeting, pricing)
- System prompt vs user prompt architecture
- Structured output extraction (JSON mode, Pydantic validation)
- Streaming responses (`stream=True`) for long outputs
- Context window management (what to include vs summarise)
- Prompt chaining (data fetch → clean → enrich → generate)
- Tool calling basics (giving the model a search function)
- Error handling for LLM outputs (retries, validation fallbacks)

### Deliverable
FastAPI endpoint `POST /brief/{company_name}` + Streamlit UI with form input and formatted brief display.

---

## Plugin 2 — Multi-Agent Orchestrator

**Phase:** 2 (Months 3–4)
**Status when complete:** Full agentic research workflow

### What You Build
A LangGraph-orchestrated multi-agent workflow where 4 specialised agents run in sequence, passing state to each other, to produce a richer output than any single LLM call could achieve.

### Agent Graph

```
company_name
    │
    ▼
[Trial Agent] ──────────────────────────────────────┐
  Queries ClinicalTrials.gov                         │
  Extracts: active protocols, phases, sites          │
    │                                                │
    ▼                                                ▼
[Intel Agent]                                  shared_state{}
  Uses web_search MCP tool                           │
  Extracts: news, pipeline, M&A, partnerships        │
    │                                                │
    ▼                                                │
[Fit Scorer Agent] ◄─────────────────────────────────┘
  Scores sponsor vs CRO capability profile
  Output: score 0–100 + rationale per dimension
    │
    ▼
[Outreach Drafter Agent]
  Uses all prior context + RAG retrieval (Plugin 3)
  Output: personalised BD outreach email
```

### LangGraph Structure

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ARIAState(TypedDict):
    company_name: str
    trial_data: dict
    intel_data: dict
    fit_score: dict          # {score: int, rationale: str, dimensions: dict}
    outreach_draft: str
    errors: List[str]

def build_aria_graph():
    graph = StateGraph(ARIAState)
    
    graph.add_node("trial_agent", trial_agent_node)
    graph.add_node("intel_agent", intel_agent_node)
    graph.add_node("fit_scorer", fit_scorer_node)
    graph.add_node("outreach_drafter", outreach_drafter_node)
    
    graph.set_entry_point("trial_agent")
    graph.add_edge("trial_agent", "intel_agent")
    graph.add_edge("intel_agent", "fit_scorer")
    graph.add_edge("fit_scorer", "outreach_drafter")
    graph.add_edge("outreach_drafter", END)
    
    return graph.compile()
```

### MCP Tool Use Pattern

```python
# Registering web_search as an Anthropic tool
tools = [
    {
        "type": "web_search_20250305",
        "name": "web_search"
    }
]

# Intel Agent using the tool
def intel_agent_node(state: ARIAState) -> ARIAState:
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1500,
        tools=tools,
        messages=[{
            "role": "user",
            "content": f"Search for recent news about {state['company_name']}'s clinical pipeline, partnerships, and CRO relationships."
        }]
    )
    # Handle tool_use blocks in response
    ...
```

### Fit Scoring Dimensions

```python
FIT_DIMENSIONS = {
    "therapeutic_area_match": {"weight": 0.30},  # Sponsor TA vs CRO expertise
    "phase_capability":       {"weight": 0.25},  # Phase I/II/III/IV match
    "geographic_overlap":     {"weight": 0.20},  # Trial sites vs CRO footprint
    "deal_size_fit":          {"weight": 0.15},  # Estimated trial budget
    "competitive_timing":     {"weight": 0.10},  # How soon they need a CRO
}
```

### AI Skills Learned (Phase 2)
- Multi-agent architecture patterns (sequential, parallel, hierarchical)
- LangGraph: nodes, edges, state schema, conditional routing
- MCP (Model Context Protocol): tool registration, tool_use/tool_result handling
- ReAct pattern (Reasoning + Acting in a loop)
- Agent state management across steps
- Handling tool call failures and agent retries
- Prompt design for agents with specific roles
- Observability: tracing agent runs with LangSmith

---

## Plugin 3 — RAG Knowledge Layer

**Phase:** 3 (Months 5–6)
**Status when complete:** Context-aware, evidence-backed outputs

### What You Build
A vector store–backed retrieval layer that gives the Outreach Drafter Agent access to a corpus of past proposals, capability docs, and win/loss notes. The agent cites relevant precedents in its output.

### Corpus (Synthetic — Generate with Claude)
- 50 past proposal summaries (vary by TA, phase, geography, outcome)
- 10 CRO capability statements (one per therapeutic area)
- 20 win/loss case notes
- FDA guidance documents (public, free)
- Relevant ICH guidelines (public, free)

### RAG Pipeline

```python
# Ingestion
from anthropic import Anthropic
import pinecone  # or pgvector via psycopg2

def ingest_corpus(docs: List[Document]):
    for doc in docs:
        # 1. Chunk (recursive, 512 tokens, 10% overlap)
        chunks = chunk_document(doc, size=512, overlap=50)
        
        # 2. Embed (use Anthropic or OpenAI embeddings)
        embeddings = embed_chunks(chunks)  # voyage-3 recommended
        
        # 3. Store with metadata
        pinecone_index.upsert([
            (chunk.id, embedding, {
                "text": chunk.text,
                "doc_type": doc.type,        # proposal / capability / win_loss
                "therapeutic_area": doc.ta,
                "phase": doc.phase,
                "outcome": doc.outcome,      # won / lost / ongoing
                "year": doc.year
            })
            for chunk, embedding in zip(chunks, embeddings)
        ])

# Retrieval (hybrid: dense + sparse)
def retrieve_relevant_context(query: str, filters: dict, top_k: int = 5):
    dense_results = pinecone_index.query(
        vector=embed(query),
        filter=filters,
        top_k=top_k,
        include_metadata=True
    )
    return rerank(dense_results, query)  # cohere rerank or cross-encoder
```

### Upgrading the Outreach Drafter Agent

```python
def outreach_drafter_node(state: ARIAState) -> ARIAState:
    # Retrieve relevant past proposals
    context = retrieve_relevant_context(
        query=f"{state['company_name']} {state['trial_data']['therapeutic_area']}",
        filters={"therapeutic_area": state['trial_data']['therapeutic_area']},
        top_k=3
    )
    
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1000,
        system="You are a CRO BD director writing personalised sponsor outreach.",
        messages=[{
            "role": "user",
            "content": f"""
            Sponsor: {state['company_name']}
            Fit score: {state['fit_score']['score']}/100
            Key signals: {state['intel_data']['key_signals']}
            
            Relevant past work (use as evidence, cite specifically):
            {context}
            
            Write a personalised BD outreach email that:
            1. References a specific aspect of their pipeline
            2. Cites a relevant past study we ran
            3. Proposes a concrete next step
            """
        }]
    )
    ...
```

### Evaluation Harness

```python
# RAGAS evaluation (do not skip this — it's what makes RAG trustworthy)
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision

test_questions = [
    "What oncology Phase II studies has the CRO run in Europe?",
    "Do we have experience with rare disease sponsors?",
    ...
]

results = evaluate(
    dataset=test_dataset,
    metrics=[faithfulness, answer_relevancy, context_precision]
)
```

### AI Skills Learned (Phase 3)
- Embedding models: selection, dimensionality, cost trade-offs
- Chunking strategies: fixed, recursive, semantic, document-aware
- Vector databases: Pinecone, pgvector (and when to use each)
- Hybrid search: dense (semantic) + sparse (BM25) retrieval
- Re-ranking: cross-encoders, Cohere rerank
- RAG evaluation: RAGAS metrics (faithfulness, relevancy, precision)
- LLM observability: LangSmith tracing, prompt versioning
- When to fine-tune vs prompt + retrieve (the core RAG vs fine-tuning decision)

---

## Plugin 4 — Production SaaS Shell

**Phase:** 4 (Months 7–9)
**Status when complete:** Deployable product with real users

### What You Build
A multi-tenant SaaS wrapper around Plugins 1–3, with proper auth, usage metering, a clean UI, and live MCP integrations for Gmail and Google Calendar.

### Tech Stack

```
Backend:    FastAPI + SQLAlchemy + PostgreSQL
Auth:       JWT (python-jose) + API key management
Frontend:   Streamlit (rapid) or Next.js (polished)
Infra:      Docker + Railway / Render / AWS EC2
Metering:   Usage tracked per org/user, cost per query logged
MCPs:       Gmail MCP + Google Calendar MCP (already connected)
```

### FastAPI Application Structure

```
aria/
├── main.py                  # FastAPI app entry point
├── routers/
│   ├── auth.py              # JWT login, API key generation
│   ├── brief.py             # POST /brief/{company_name}
│   ├── research.py          # POST /research/run (full agent workflow)
│   └── history.py           # GET /history (past runs per org)
├── agents/
│   ├── graph.py             # LangGraph ARIA graph definition
│   ├── trial_agent.py
│   ├── intel_agent.py
│   ├── fit_scorer.py
│   └── outreach_drafter.py
├── rag/
│   ├── ingest.py
│   ├── retrieval.py
│   └── evaluate.py
├── mcp/
│   ├── gmail.py             # Gmail MCP: draft and stage emails
│   └── calendar.py          # Calendar MCP: create follow-up slots
├── db/
│   ├── models.py            # User, Org, Run, UsageLog
│   └── session.py
└── config.py
```

### Gmail MCP Integration

```python
# Stage the outreach draft directly into the user's Gmail
async def stage_outreach_email(
    to: str,
    subject: str,
    body: str,
    user_gmail_token: str
):
    """Uses Gmail MCP to create a draft in the BD rep's Gmail account."""
    response = await anthropic_api_call_with_mcp(
        mcp_server_url="https://gmail.mcp.claude.com/mcp",
        instruction=f"Create a draft email to {to} with subject '{subject}' and body: {body}",
        user_token=user_gmail_token
    )
    return response
```

### Google Calendar MCP Integration

```python
# Create a follow-up meeting slot
async def create_followup_slot(
    sponsor_name: str,
    rep_email: str,
    suggested_date: str
):
    """Uses Calendar MCP to create a 30-min discovery call slot."""
    response = await anthropic_api_call_with_mcp(
        mcp_server_url="https://gcal.mcp.claude.com/mcp",
        instruction=f"Create a 30-minute meeting titled 'ARIA Follow-up: {sponsor_name}' on {suggested_date} and invite {rep_email}",
    )
    return response
```

### Usage Metering

```python
# Track cost per run (critical for SaaS unit economics)
class UsageLog(Base):
    id = Column(UUID, primary_key=True)
    org_id = Column(UUID, ForeignKey("orgs.id"))
    run_id = Column(UUID)
    plugin = Column(String)          # plugin_1 / plugin_2 / plugin_3
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    estimated_cost_usd = Column(Float)
    created_at = Column(DateTime)

# Cost per query target: < $0.15 per full ARIA run
# Pricing suggestion: $199/month for 100 runs = $1.99/run
# Margin at $0.15 COGS: ~92%
```

### Deployment (Minimum Viable)

```bash
# Docker
FROM python:3.12-slim
COPY . /app
RUN pip install -r requirements.txt
CMD ["uvicorn", "aria.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Railway (simplest cloud deploy)
railway init
railway up
```

### AI Skills Learned (Phase 4)
- AI systems design: latency budgets, token cost modelling, caching strategies
- Multi-tenant architecture for LLM apps (isolating context per user/org)
- MCP integration in production (auth flows, error handling, rate limits)
- Streaming responses to a UI (FastAPI `StreamingResponse` + Streamlit `st.write_stream`)
- Prompt versioning and A/B testing in production
- Cost instrumentation (input/output token tracking per request)
- LLM-aware API design (async-first, timeout handling, fallback models)

---

## Full Tech Stack Reference

| Category | Technology | Plugin |
|---|---|---|
| LLM API | `anthropic` Python SDK | 1, 2, 3, 4 |
| Agent orchestration | LangGraph | 2, 3, 4 |
| Tool use / MCP | Anthropic tool_use, MCP protocol | 2, 4 |
| Embeddings | Voyage-3 (Anthropic) or text-embedding-3 | 3 |
| Vector DB | Pinecone (cloud) or pgvector (self-hosted) | 3 |
| RAG evaluation | RAGAS, LangSmith | 3 |
| Re-ranking | Cohere Rerank or cross-encoder | 3 |
| Backend API | FastAPI + Uvicorn | 1, 4 |
| Frontend | Streamlit (Phase 1–3), Next.js optional (Phase 4) | 1, 4 |
| Auth | JWT (python-jose), API keys | 4 |
| Database | PostgreSQL + SQLAlchemy | 4 |
| Observability | LangSmith, custom UsageLog | 3, 4 |
| Deployment | Docker + Railway / Render | 4 |
| Data fetching | `httpx` (async HTTP) | 1, 2 |
| Data validation | Pydantic v2 | 1, 2, 3, 4 |

---

## Project Milestones

| Milestone | Plugin | Deliverable |
|---|---|---|
| Week 4 | 1 | `generate_brief("Pfizer")` returns valid JSON |
| Week 6 | 1 | FastAPI endpoint + Streamlit UI live locally |
| Week 10 | 2 | Full 4-agent LangGraph workflow runs end-to-end |
| Week 12 | 2 | MCP web search tool integrated in Intel Agent |
| Week 18 | 3 | RAG corpus ingested, retrieval scoring >0.75 on RAGAS |
| Week 20 | 3 | Outreach drafts cite specific past proposals |
| Week 28 | 4 | Multi-tenant FastAPI + Streamlit app deployed |
| Week 32 | 4 | Gmail + Calendar MCPs live, first 5 real users |
| Week 36 | 4 | First paying customer at $199/month |

---

## AI Engineering Concepts Covered

This single project gives you hands-on exposure to:

- **LLM API fundamentals** — model selection, token budgeting, streaming, structured outputs
- **Prompt engineering** — system prompts, few-shot examples, chain-of-thought, role prompting
- **Tool use & function calling** — Anthropic tool_use format, MCP protocol
- **Agentic patterns** — ReAct, Plan-and-Execute, multi-agent handoffs, shared state
- **RAG fundamentals** — chunking, embedding, hybrid retrieval, re-ranking, evaluation
- **LLM observability** — tracing, prompt versioning, cost tracking, LangSmith
- **AI systems design** — latency budgets, caching, fallback strategies, multi-tenancy
- **Production deployment** — Docker, async APIs, streaming UI, auth, usage metering
- **AI evaluation** — RAGAS, automated test harnesses, regression testing for LLM outputs

---

## Notes for Claude Code Sessions

- **Start each session** by pasting this document or linking it as context
- **Session structure suggestion:** one plugin per Claude Code project scope
- **Ask Claude Code to:** scaffold the folder structure, write agent node functions, debug LangGraph state issues, write RAGAS test cases
- **Key constraint:** always track token usage per call — build `UsageLog` from Plugin 1 onward, not as an afterthought
- **Synthetic data generation:** use Claude (claude.ai) to generate the proposal corpus before starting Plugin 3 — create 50 varied one-page summaries covering different TAs, phases, and outcomes

---

*Document version: 1.0 — generated from ARIA Capstone planning session, April 2026*
