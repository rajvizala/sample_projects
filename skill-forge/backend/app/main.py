from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import get_settings
from .database import init_db
from .routers import learners_router, coach_router, graph_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="SkillForge API",
    description="Adaptive AI upskilling platform with Neo4J knowledge graph",
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

app.include_router(learners_router, prefix="/api")
app.include_router(coach_router, prefix="/api")
app.include_router(graph_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "SkillForge API"}
