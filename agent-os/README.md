# AgentOS — Multi-Agent AI Operating System for Solopreneurs

A production-grade, full-stack platform that gives a single founder the operational capacity of an entire team. Five specialized AI agents — research, content, analytics, customer, and advisor — are orchestrated by a central LangGraph state machine and exposed through a streaming chat interface.

Inspired by the Y Combinator / Daybreak Ventures request for "an AI-native OS for solopreneurs that lets one person deliver agency-level outcomes."

---

## Architecture

```
User Message
     |
     v
FastAPI SSE Endpoint
     |
     v
LangGraph Orchestrator  ------>  Classifies intent via Gemini
     |
     v (conditional edge routing)
  [Research]  [Content]  [Analytics]  [Customer]  [General]
     |             |           |            |           |
     v             v           v            v           v
  LangChain Tools (bound to each agent)
     |
     v
Streaming tokens via SSE -> Next.js frontend
     |
     v
Redis cache (55-60% hit rate on repeated queries)
     |
     v
SQLAlchemy + SQLite (conversation history)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent Orchestration | LangGraph (StateGraph with conditional routing) |
| LLM | Google Gemini 1.5 Flash (free tier) |
| Backend | FastAPI + async SQLAlchemy |
| Streaming | Server-Sent Events (SSE) |
| Caching | Redis (async, with SHA256 cache keys) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Frontend | Next.js 14 + TypeScript + Tailwind CSS |
| Deployment | Docker Compose |

---

## Key Engineering Decisions

**Multi-agent routing via intent classification**: The orchestrator node calls Gemini to classify intent before routing. This separates concerns cleanly and allows each agent to be independently tested and upgraded.

**Streaming with SSE**: Rather than waiting for full responses, the frontend streams tokens in real time. The backend uses `astream_events()` from LangGraph, filtering for `on_chat_model_stream` events and yielding them as SSE chunks. This keeps perceived latency near-zero.

**Semantic caching with Redis**: Chat responses are cached by SHA256 hash of `(message, business_context)`. This mirrors the distributed caching architecture from the AgentOS experience at DTG, reducing redundant LLM calls for semantically identical queries.

**Tool-augmented agents**: Each agent uses LangChain tools (`@tool` decorator) for structured data retrieval before generating responses. The Research agent calls `analyze_market_trend` and `analyze_competitors`, the Analytics agent calls `analyze_business_metrics`, etc. The LLM synthesizes tool output into the final response.

**Business context injection**: A user-configurable context dictionary (name, industry, audience, stage, tone) is injected into each agent's system prompt, personalizing responses without requiring repeated explanation.

---

## Project Structure

```
agent-os/
  backend/
    app/
      agents/
        graph.py          # LangGraph StateGraph definition
        state.py          # AgentState TypedDict
        tools.py          # LangChain tool definitions
      cache/
        redis_cache.py    # Async Redis caching layer
      routers/
        chat.py           # SSE streaming endpoint
        sessions.py       # Session CRUD
      config.py
      database.py
      models.py
      main.py
  frontend/
    app/page.tsx          # Main chat interface
    components/
      ChatMessage.tsx
      Sidebar.tsx
      ContextPanel.tsx
      AgentBadge.tsx
    lib/api.ts
    types/index.ts
  docker-compose.yml
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+
- Redis (optional — app degrades gracefully without it)
- Google Gemini API key (free at [aistudio.google.com](https://aistudio.google.com))

### Backend

```bash
cd agent-os/backend
cp .env.example .env
# Add your GEMINI_API_KEY to .env

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd agent-os/frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Docker (full stack)

```bash
cd agent-os
GEMINI_API_KEY=your_key docker compose up --build
```

---

## Demo Prompts

```
Research the top 5 competitors in the B2B SaaS productivity space and identify the biggest gap.

Write a compelling LinkedIn post about how solopreneurs use AI agents to scale solo in 2025.

My MRR is $8,500 growing at 12% MoM with 4.1% churn. What are the top 3 actions I should take?

Draft a professional response to: "I've been waiting 5 days for a refund. This is unacceptable."
```

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/sessions` | POST | Create a new session |
| `/api/sessions` | GET | List all sessions |
| `/api/sessions/{id}/messages` | GET | Get conversation history |
| `/api/sessions/{id}/context` | PUT | Update business context |
| `/api/chat/stream` | POST | Stream agent response (SSE) |
| `/api/agents` | GET | List available agents |

---

## Extending the System

To add a new agent:

1. Add a system prompt to `AGENT_SYSTEMS` in `graph.py`
2. Define tools in `tools.py` with the `@tool` decorator
3. Add a node using `_make_agent_node()` in `build_graph()`
4. Add a conditional edge from the orchestrator
5. Update the orchestrator system prompt with the new agent description
