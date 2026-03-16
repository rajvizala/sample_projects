# AgentForge - Multi-Agent Orchestration Platform

A production-grade platform for building, deploying, and orchestrating AI agent workflows.
AgentForge enables solopreneurs and small teams to compose specialized AI agents into
powerful automated pipelines -- delivering agency-level outcomes with software-like margins.

**Inspired by:** Bo Berluti (VP at RTP) calling for AI-native operating systems for
solopreneurs, and Jessica Peltz Zatulove (Managing Partner at Hannah Grey) seeking
orchestration platforms for "Emergent Organizations" with hybrid AI-human structures.

---

## Architecture

```
+------------------+     +--------------------+     +-------------------+
|                  |     |                    |     |                   |
|  React Frontend  +---->+  FastAPI Backend   +---->+  Workflow Engine   |
|  (Workflow UI)   |     |  (REST + WS)      |     |  (DAG Executor)   |
|                  |     |                    |     |                   |
+------------------+     +--------+-----------+     +---+------+--------+
                                  |                     |      |
                         +--------v---------+     +-----v+  +--v--------+
                         |                  |     |      |  |           |
                         |  SQLite / PG     |     |Agents|  | Tool      |
                         |  (State Store)   |     |      |  | Registry  |
                         |                  |     +------+  |           |
                         +------------------+               +-----------+
```

### Core Components

1. **Workflow Engine** - DAG-based execution engine that routes tasks between agents,
   manages dependencies, handles retries and failures, and tracks execution state.
   Supports parallel execution of independent nodes.

2. **Agent Runtime** - Sandboxed execution environment for agents with tool access,
   memory management, and context passing. Each agent declares its capabilities,
   required inputs, and output schema.

3. **Built-in Agents**:
   - **Research Agent** - Web search, content extraction, and summarization
   - **Writer Agent** - Content generation (articles, emails, reports)
   - **Data Analyst Agent** - CSV/JSON analysis, chart generation, insights
   - **Code Agent** - Code generation, review, and transformation
   - **Coordinator Agent** - Meta-agent that breaks complex tasks into sub-tasks

4. **Tool Registry** - Extensible tool system where agents can access web search,
   file I/O, HTTP requests, code execution, and custom tools.

5. **Memory System** - Short-term (per-execution) and long-term (persistent)
   memory with vector similarity search for context retrieval.

---

## Tech Stack

| Layer       | Technology                                          |
|-------------|-----------------------------------------------------|
| Backend     | FastAPI, SQLAlchemy, Pydantic, WebSockets            |
| Engine      | Custom DAG executor, asyncio, concurrent.futures     |
| AI/LLM      | Google Gemini (free), extensible to any LLM API      |
| Database    | SQLite (dev) / PostgreSQL (prod)                     |
| Frontend    | React 18, Tailwind CSS, Vite                         |
| Infra       | Docker, Docker Compose                               |

---

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker

```bash
docker-compose up --build
```

### Environment Variables

| Variable         | Description                              | Required |
|------------------|------------------------------------------|----------|
| GEMINI_API_KEY   | Google Gemini API key for LLM agents     | No       |
| DATABASE_URL     | Database connection string               | No       |
| SECRET_KEY       | JWT secret                               | No       |

---

## API Endpoints

| Method | Endpoint                           | Description                          |
|--------|------------------------------------|--------------------------------------|
| GET    | `/api/v1/agents`                   | List available agents                |
| GET    | `/api/v1/agents/{id}`              | Get agent details and capabilities   |
| POST   | `/api/v1/agents/{id}/execute`      | Execute a single agent               |
| GET    | `/api/v1/workflows`                | List workflows                       |
| POST   | `/api/v1/workflows`                | Create a new workflow                |
| GET    | `/api/v1/workflows/{id}`           | Get workflow details                 |
| POST   | `/api/v1/workflows/{id}/execute`   | Execute a workflow                   |
| GET    | `/api/v1/executions`               | List execution history               |
| GET    | `/api/v1/executions/{id}`          | Get execution details and logs       |
| GET    | `/api/v1/tools`                    | List available tools                 |
| WS     | `/ws/executions/{id}`              | Real-time execution updates          |

---

## Creating Custom Agents

```python
from app.agents.base import BaseAgent, AgentCapability

class MyAgent(BaseAgent):
    name = "my_agent"
    description = "Does something useful"
    capabilities = [AgentCapability.TEXT_GENERATION]

    async def execute(self, input_data: dict, context: dict) -> dict:
        # Your agent logic here
        return {"result": "output"}
```

---

## Project Structure

```
agentforge/
  backend/
    app/
      agents/       # Agent implementations
      api/          # Route handlers
      core/         # Config, database
      engine/       # DAG executor, workflow runtime
      models/       # SQLAlchemy models
      schemas/      # Pydantic schemas
      services/     # Business logic
      main.py       # FastAPI entry
    tests/
    requirements.txt
  frontend/
    src/
      components/   # UI components
      utils/        # API client
  docker-compose.yml
  Dockerfile
```

---

## License

MIT
