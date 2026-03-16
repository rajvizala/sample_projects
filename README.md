# Portfolio Projects

Three production-grade projects targeting FullStack/Backend Engineering and AI/ML roles. Each is inspired by real startup requests from top VC firms and demonstrates distinct, non-generic technical depth.

---

## Projects

### 1. [AgentOS](./agent-os/) — Multi-Agent AI Operating System

**Target role**: Full-Stack + AI/ML Engineering

A solopreneur platform where five specialized LangGraph agents (Research, Content, Analytics, Customer, Advisor) are orchestrated by a central state machine and exposed through a streaming chat interface.

**Key technical depth**:
- LangGraph multi-agent orchestration with conditional routing
- Streaming Server-Sent Events from LangGraph `astream_events()`
- Distributed caching with async Redis (SHA256 semantic cache keys)
- Tool-augmented agents with LangChain `@tool` decorator
- Business context injection into agent system prompts

**Stack**: FastAPI, LangGraph, LangChain, Google Gemini, Redis, SQLAlchemy, Next.js, TypeScript, Tailwind

---

### 2. [SecureSignal](./secure-signal/) — Real-Time AI Threat Detection

**Target role**: Backend Engineering + AI/ML Engineering

A personal security monitor that detects AI-generated scams, phishing, and account takeover attempts in real time. The ML detection engine runs entirely locally — no API costs required.

**Key technical depth**:
- Statistical AI text detection via perplexity (entropy analysis) and burstiness (sentence length variance)
- Multi-layer phishing detection: 50+ regex patterns across 5 threat categories
- WebSocket-based real-time threat broadcasting with auto-reconnect
- Composite risk scoring with explainability
- Async background monitoring loop with asyncio tasks

**Stack**: FastAPI, WebSockets, scikit-learn, SQLAlchemy, Next.js, TypeScript, Tailwind

---

### 3. [SkillForge](./skill-forge/) — Adaptive AI Upskilling Coach

**Target role**: AI/ML Engineering + Full-Stack Engineering

A knowledge-graph-powered learning platform that maps AI/ML skills as a directed graph in Neo4J, computes personalized learning paths via BFS traversal, and delivers adaptive coaching through a streaming LangGraph agent.

**Key technical depth**:
- Neo4J knowledge graph with 20 skill nodes and 25 directed weighted edges
- BFS-based learning path optimization from mastered skills to targets
- Adaptive assessment: Gemini grades answers, identifies gaps, adapts difficulty
- D3.js force-directed graph visualization with drag, zoom, and click interactions
- Mastery detection auto-updates the knowledge graph and awards XP

**Stack**: FastAPI, Neo4J, LangGraph, Google Gemini, D3.js, Next.js, TypeScript, Tailwind

---

## Quick Start (any project)

```bash
# 1. Clone and navigate to a project
cd agent-os   # or secure-signal, skill-forge

# 2. Copy env files
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local

# 3. Add your Gemini API key to backend/.env
# Get one free at: https://aistudio.google.com

# 4. Run with Docker
GEMINI_API_KEY=your_key docker compose up --build

# OR run manually:
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
cd frontend && npm install && npm run dev
```

---

## Gemini API (Free Tier)

All three projects use Google Gemini 1.5 Flash, which is available on the free tier:
- 15 requests per minute
- 1 million tokens per day
- No credit card required

Get your key at [aistudio.google.com](https://aistudio.google.com)

SecureSignal's core threat detection (phishing + AI text detection) requires **no API key** and works offline.
