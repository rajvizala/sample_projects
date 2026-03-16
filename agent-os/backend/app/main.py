from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import get_settings
from .database import init_db
from .routers import sessions_router, chat_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="AgentOS API",
    description="Multi-agent AI operating system for solopreneurs",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions_router, prefix="/api")
app.include_router(chat_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "AgentOS API"}


@app.get("/api/agents")
async def list_agents():
    return {
        "agents": [
            {
                "id": "research",
                "name": "Research Agent",
                "description": "Market analysis, competitor intelligence, trend mapping",
                "icon": "Search",
                "color": "#6366f1"
            },
            {
                "id": "content",
                "name": "Content Agent",
                "description": "Blog posts, email campaigns, social copy, landing pages",
                "icon": "PenTool",
                "color": "#10b981"
            },
            {
                "id": "analytics",
                "name": "Analytics Agent",
                "description": "Business metrics, KPI analysis, growth forecasting",
                "icon": "BarChart2",
                "color": "#f59e0b"
            },
            {
                "id": "customer",
                "name": "Customer Agent",
                "description": "Support responses, complaint handling, follow-ups",
                "icon": "MessageSquare",
                "color": "#ec4899"
            },
            {
                "id": "general",
                "name": "Business Advisor",
                "description": "Strategy, operations, and general business guidance",
                "icon": "Briefcase",
                "color": "#3b82f6"
            }
        ]
    }
