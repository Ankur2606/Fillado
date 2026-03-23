# Fillado — ET Intelligence Layer

> **Modular AI system that turns ET Markets data into actionable signals for Indian retail and pro investors.**

---

## Table of Contents

1. [Overview](#overview)
2. [Products](#products)
3. [Architecture](#architecture)
4. [Repository Structure](#repository-structure)
5. [Prerequisites](#prerequisites)
6. [Quick Start](#quick-start)
7. [Environment Variables](#environment-variables)
8. [Running the Dev Server](#running-the-dev-server)
9. [API Reference](#api-reference)
10. [Contributing](#contributing)
11. [License](#license)

---

## Overview

Fillado ET Intelligence Layer ingests vernacular + English news, ET archives, live NSE data, and corporate events. It builds a **causal graph** of companies, events, and price moves, then exposes four AI-powered products to help investors act ahead of the market.

---

## Products

### 1. Opportunity Radar
Cross-lingual, event-driven radar that tracks filings, insider trades, vernacular news, and supply-chain shocks to surface high-confidence trade signals before the market reacts.

**Agents involved:** `HyperLocalScout`, `VerificationAgent`, `CausalMapper`

### 2. Chart Pattern Intelligence
Real-time NSE pattern scanner with plain-English explanations and per-stock back-tests. Detects classical chart patterns (Head & Shoulders, Cup & Handle, etc.) and explains them in human-readable language.

### 3. Market ChatGPT 2.0
Portfolio-aware, multi-step research assistant grounded in ET data, the causal graph, and historical patterns. Prioritises holdings from the user's portfolio when retrieving context.

### 4. AI Market Video Engine
Auto-generated, script-to-video daily market wraps and flow visualizations. Produces structured video jobs from market summaries using a modular script → shot-plan → render pipeline.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                   FastAPI (async)                     │
│  /alerts  /chart-patterns  /market-chatgpt  /videos  │
└──────────────┬───────────────────────────────────────┘
               │
     ┌─────────▼─────────┐
     │  LangGraph Agents  │  (stateful, multi-step workflows)
     └─────────┬─────────┘
               │
   ┌───────────┼────────────────┐
   ▼           ▼                ▼
Neo4j       Pinecone/Milvus   PostgreSQL
(causal     (embeddings)      (users, portfolios,
 graph)                        alert logs, video jobs)
                                     │
                                   Redis
                             (pub/sub, task queue)
```

**Tech stack:**

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Web Framework | FastAPI |
| Orchestration | LangGraph |
| LLM | Provider-agnostic (Gemini / OpenAI / DeepSeek) |
| Knowledge Graph | Neo4j |
| Vector DB | Pinecone or Milvus |
| Relational DB | PostgreSQL (asyncpg) |
| Cache / Pub-Sub | Redis |

---

## Repository Structure

```
Fillado/
├── .env.example
├── .gitignore
├── config.py                  # Pydantic BaseSettings
├── main.py                    # FastAPI app + router wiring
├── requirements.txt
├── README.md
└── app/
    ├── api/
    │   ├── __init__.py
    │   ├── alerts.py          # GET /alerts, POST /test-signal
    │   ├── chart_patterns.py  # GET /chart-patterns/{symbol}
    │   ├── market_chatgpt.py  # POST /market-chatgpt/query
    │   └── videos.py          # POST /videos/daily-wrap, GET /videos/{job_id}
    ├── services/
    │   ├── opportunity_radar/
    │   │   ├── __init__.py
    │   │   ├── ingestion_sources.py
    │   │   ├── agents.py      # HyperLocalScout, VerificationAgent, CausalMapper
    │   │   └── models.py      # Event, Company, Alert
    │   ├── chart_patterns/
    │   │   ├── __init__.py
    │   │   ├── pattern_detector.py
    │   │   ├── backtest_engine.py
    │   │   ├── explanations.py
    │   │   └── models.py      # PatternHit, PatternStats
    │   ├── market_chatgpt/
    │   │   ├── __init__.py
    │   │   ├── tools.py
    │   │   ├── workflows.py   # LangGraph market_research graph
    │   │   └── models.py
    │   └── video_engine/
    │       ├── __init__.py
    │       ├── script_generator.py
    │       ├── shot_planner.py
    │       ├── renderer_stub.py
    │       └── models.py      # VideoJob, VideoScript
    ├── core/
    │   ├── graph/
    │   │   ├── __init__.py
    │   │   ├── neo4j_client.py
    │   │   └── schema.py
    │   ├── embeddings/
    │   │   ├── __init__.py
    │   │   └── vector_client.py
    │   └── db/
    │       ├── __init__.py
    │       ├── postgres.py
    │       └── redis_client.py
    └── workers/
        ├── __init__.py
        ├── alert_worker.py
        └── video_worker.py
```

---

## Prerequisites

- Python 3.11+
- Docker (recommended for Neo4j, PostgreSQL, Redis)
- A running Neo4j instance
- A Pinecone or Milvus account / instance
- PostgreSQL database
- Redis server

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/Ankur2606/Fillado.git
cd Fillado

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and fill in all required values

# 5. Run the development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values. See [.env.example](.env.example) for the full list of required variables.

Key categories:

| Category | Variables |
|---|---|
| LLM Keys | `OPENAI_API_KEY`, `GEMINI_API_KEY`, `DEEPSEEK_API_KEY` |
| Neo4j | `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` |
| Vector DB | `PINECONE_API_KEY`, `PINECONE_ENV`, `MILVUS_URI` |
| PostgreSQL | `DATABASE_URL` |
| Redis | `REDIS_URL` |

---

## Running the Dev Server

```bash
# Standard (with auto-reload)
uvicorn main:app --reload

# With custom host/port
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production (multiple workers)
uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000
```

Once running, visit:
- **API Docs (Swagger UI):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health check:** http://localhost:8000/health

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health check |
| `GET` | `/alerts` | List active trade signals from Opportunity Radar |
| `POST` | `/test-signal` | Manually inject an event to test the signal pipeline |
| `GET` | `/chart-patterns/{symbol}` | Get detected chart patterns for an NSE symbol |
| `POST` | `/market-chatgpt/query` | Submit a portfolio-aware research query |
| `POST` | `/videos/daily-wrap` | Trigger generation of a daily market wrap video |
| `GET` | `/videos/{job_id}` | Get status and result of a video generation job |

Full interactive documentation is available at `/docs` when the server is running.

---

## Contributing

1. Fork the repository and create a feature branch.
2. Follow the existing module structure for new features.
3. Add `# TODO:` comments for domain-specific logic that needs real data sources.
4. Open a Pull Request with a clear description of the changes.

---

## License

[MIT](LICENSE)
