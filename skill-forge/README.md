# SkillForge — Adaptive AI Upskilling Coach with Knowledge Graph

An intelligent learning platform that maps AI/ML skills as a directed knowledge graph in Neo4J, computes personalized learning paths using graph traversal, and provides adaptive 1:1 coaching through a LangGraph-powered conversational AI agent.

Inspired by the Supercharge VC request for "a personal trainer for AI adoption — an always-on agent that monitors activity, powers relevant AI upskilling, and holds users accountable."

---

## Architecture

```
Learner Profile
     |
     v
Neo4J Knowledge Graph  <-- 20 AI/ML skill nodes, 25 directed edges
     |
     v
Path Optimizer  <-- BFS + weighted traversal from mastered -> target skills
     |
     v
Personalized Learning Path (ordered, estimated hours, difficulty)
     |
     v
LangGraph Coach Agent
  - System prompt injected with learner profile + current skill
  - Skill-specific assessment question bank
  - Streaming response via SSE
  - Mastery detection -> auto-updates skill graph
     |
     v
D3.js Force Graph Visualization
  - Interactive node selection
  - Visual mastered/unmastered state
  - Draggable, zoomable graph
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Knowledge Graph | Neo4J (Bolt protocol, in-memory fallback) |
| Graph Traversal | Custom BFS with weighted edges |
| Coach Agent | LangGraph + Google Gemini 1.5 Flash |
| Backend | FastAPI + async SQLAlchemy |
| Streaming | Server-Sent Events |
| Frontend | Next.js 14 + TypeScript + Tailwind CSS |
| Graph Visualization | D3.js (force-directed layout) |
| Deployment | Docker Compose with Neo4J Community |

---

## Knowledge Graph Design

The skill graph models AI/ML knowledge as a directed weighted graph:

**Nodes**: 20 skills across 7 categories (programming, machine_learning, deep_learning, llm, frameworks, infrastructure, engineering)

**Edge Types**:
- `PREREQUISITE_FOR`: Must learn before proceeding (weight 1.0)
- `LEADS_TO`: Natural next step after mastery (weight 0.7-0.9)
- `RELATED_TO`: Conceptually connected (weight 0.5-0.7)
- `REQUIRES`: Dependency relationship (weight 0.9-1.0)
- `USED_IN` / `USED_WITH`: Tool relationships (weight 0.7-0.9)

**Sample graph excerpt**:
```
python_basics -[PREREQUISITE_FOR]-> ml_fundamentals
ml_fundamentals -[PREREQUISITE_FOR]-> neural_networks
neural_networks -[PREREQUISITE_FOR]-> transformers
transformers -[LEADS_TO]-> llm_basics
llm_basics -[LEADS_TO]-> prompt_engineering
prompt_engineering -[LEADS_TO]-> langchain
langchain -[LEADS_TO]-> langgraph
langgraph -[USED_FOR]-> ai_agents
rag_systems -[REQUIRES]-> vector_databases
rag_systems -[REQUIRES]-> embeddings
```

### Learning Path Algorithm

```python
def compute_learning_path(mastered: set, targets: list) -> list:
    # For each target, find prerequisites not yet mastered via DFS
    # Deduplicate and order by dependency
    # Prioritize skills that unlock the most downstream nodes
    path = []
    for target in targets:
        path.extend(_find_path_to_target(mastered, target))
    return deduplicated_ordered(path)[:8]
```

---

## Adaptive Assessment System

Each skill has a curated question bank designed to test genuine understanding:

```python
ASSESSMENT_QUESTIONS = {
    "rag_systems": [
        "What is the difference between sparse (BM25) and dense retrieval? When would you use each?",
        "Walk me through chunking a 200-page PDF for a RAG pipeline.",
        "What is re-ranking in RAG and why does it improve retrieval quality?"
    ],
    "langgraph": [
        "What is a StateGraph in LangGraph and what problem does it solve over simple chains?",
        "Explain the difference between add_edge and add_conditional_edges.",
        "How does LangGraph handle state persistence across multiple agent invocations?"
    ],
    # ... 8 more skills
}
```

Gemini scores answers on a 0-1 scale, identifies correct/missing concepts, and returns adaptive follow-up questions. A score >= 0.8 automatically marks the skill as mastered and awards XP.

---

## Project Structure

```
skill-forge/
  backend/
    app/
      graph/
        knowledge_graph.py    # Skill graph, BFS path optimizer, Neo4J integration
      agents/
        coach.py              # LangGraph streaming coach + assessment
      routers/
        learners.py           # Learner CRUD + skill updates
        coach.py              # Chat stream + assessment endpoints
        graph.py              # Graph query endpoints
      models.py
      database.py
      main.py
  frontend/
    app/page.tsx              # Onboarding + 3-tab main app
    components/
      SkillGraphViz.tsx       # D3.js force-directed visualization
      CoachChat.tsx           # Streaming chat with code rendering
    lib/api.ts
    types/index.ts
  docker-compose.yml
```

---

## Getting Started

### Option 1: Without Neo4J (uses in-memory graph)

```bash
# Backend
cd skill-forge/backend
cp .env.example .env
# Add GEMINI_API_KEY to .env

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002

# Frontend
cd skill-forge/frontend
cp .env.local.example .env.local
npm install
npm run dev -- --port 3002
```

### Option 2: With Neo4J (full graph database)

```bash
cd skill-forge
GEMINI_API_KEY=your_key docker compose up --build
```

Neo4J browser available at [http://localhost:7474](http://localhost:7474)

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/learners` | POST | Create learner profile |
| `/api/learners/{id}` | GET | Get learner + computed path |
| `/api/learners/{id}/skills` | PUT | Update mastered skills |
| `/api/coach/chat/stream` | POST | Stream coaching response (SSE) |
| `/api/coach/assess` | POST | Submit + grade assessment answer |
| `/api/coach/questions/{skill_id}` | GET | Get assessment questions |
| `/api/graph` | GET | Full skill graph (nodes + edges) |
| `/api/graph/skill/{id}` | GET | Skill detail + neighbors |
| `/api/graph/path` | GET | Compute learning path |
| `/api/graph/search` | GET | Search skills |

---

## Skill Categories

| Category | Color | Example Skills |
|---|---|---|
| programming | Indigo | Python Basics, Advanced Python |
| machine_learning | Emerald | ML Fundamentals, Data Preprocessing |
| deep_learning | Amber | Neural Networks, Transformers, Fine-tuning |
| llm | Pink | LLM Basics, Prompt Engineering, RAG Systems |
| frameworks | Blue | LangChain, LangGraph |
| infrastructure | Purple | Vector Databases, Knowledge Graphs, MLOps |
| engineering | Cyan | API Integration |

---

## Extending the Graph

To add new skills, edit `AI_SKILL_GRAPH` in `knowledge_graph.py`:

```python
# Add a node
{"id": "new_skill", "label": "New Skill", "category": "llm", "difficulty": 3,
 "description": "What this skill covers"}

# Add edges
{"from": "existing_skill", "to": "new_skill", "relationship": "LEADS_TO", "weight": 0.8}
```

To add assessment questions:

```python
ASSESSMENT_QUESTIONS["new_skill"] = [
    "Your first question...",
    "Your second question..."
]
```
