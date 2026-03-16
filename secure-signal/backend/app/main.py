import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import get_settings
from .database import init_db
from .routers import analysis_router, ws_router
from .background import run_monitor

settings = get_settings()

_monitor_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _monitor_task
    await init_db()
    _monitor_task = asyncio.create_task(run_monitor(settings.monitoring_interval))
    yield
    if _monitor_task:
        _monitor_task.cancel()


app = FastAPI(
    title="SecureSignal API",
    description="Real-time personal AI threat detection and monitoring platform",
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

app.include_router(analysis_router, prefix="/api")
app.include_router(ws_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "SecureSignal API", "monitoring": "active"}


@app.get("/api/stats")
async def get_stats():
    from .database import AsyncSessionLocal
    from .models import ThreatEvent, AnalysisResult
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
        threat_count = await db.scalar(select(func.count()).select_from(ThreatEvent))
        critical_count = await db.scalar(
            select(func.count()).select_from(ThreatEvent)
            .where(ThreatEvent.severity == "CRITICAL")
        )
        analysis_count = await db.scalar(select(func.count()).select_from(AnalysisResult))
        avg_risk = await db.scalar(
            select(func.avg(ThreatEvent.risk_score)).select_from(ThreatEvent)
        )

    return {
        "total_threats_detected": threat_count or 0,
        "critical_threats": critical_count or 0,
        "analyses_run": analysis_count or 0,
        "average_risk_score": round(float(avg_risk or 0), 3),
        "monitoring_status": "active",
        "protected_channels": ["Email", "Calls", "Accounts", "Identity", "Communications"]
    }
