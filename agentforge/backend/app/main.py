"""
AgentForge - Multi-Agent Orchestration Platform
FastAPI application entry point.
"""

import json
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.database import init_db
from app.api.routes import router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multi-agent orchestration platform for building and executing AI agent workflows",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


ws_connections: dict[str, list[WebSocket]] = {}


@app.websocket("/ws/executions/{execution_id}")
async def websocket_execution(websocket: WebSocket, execution_id: str):
    """WebSocket for real-time execution updates."""
    await websocket.accept()
    ws_connections.setdefault(execution_id, []).append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_connections.get(execution_id, []).remove(websocket)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "gemini_available": bool(settings.gemini_api_key),
    }


static_path = Path(__file__).parent.parent.parent / "frontend" / "dist"
if static_path.exists():
    app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")
