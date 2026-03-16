import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from ..database import get_db
from ..models import AnalysisResult, ThreatEvent
from ..detection import compute_comprehensive_risk

router = APIRouter(prefix="/analyze", tags=["analysis"])


class AnalyzeRequest(BaseModel):
    content: str
    analysis_type: Optional[str] = "full"


class ThreatEventResponse(BaseModel):
    id: str
    threat_type: str
    severity: str
    risk_score: float
    title: str
    description: str
    source: Optional[str]
    indicators: dict
    action_required: Optional[str]
    dismissed: bool
    created_at: str


@router.post("")
async def analyze_content(body: AnalyzeRequest, db: AsyncSession = Depends(get_db)):
    if not body.content or len(body.content.strip()) < 10:
        raise HTTPException(status_code=400, detail="Content must be at least 10 characters")

    if len(body.content) > 10000:
        raise HTTPException(status_code=400, detail="Content must be under 10,000 characters")

    report = compute_comprehensive_risk(body.content, body.analysis_type or "full")

    result = AnalysisResult(
        id=str(uuid.uuid4()),
        content_snippet=body.content[:200],
        analysis_type=body.analysis_type or "full",
        risk_score=report["overall_risk_score"],
        verdict=report["overall_verdict"],
        details={
            "severity": report["severity_level"],
            "phishing_score": report["phishing_analysis"]["risk_score"],
            "ai_probability": report["ai_text_analysis"]["ai_probability"],
            "indicators": report["phishing_analysis"]["indicators"],
        }
    )
    db.add(result)
    await db.commit()

    return report


@router.get("/history")
async def get_analysis_history(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AnalysisResult).order_by(AnalysisResult.created_at.desc()).limit(limit)
    )
    items = result.scalars().all()
    return [
        {
            "id": r.id,
            "content_snippet": r.content_snippet,
            "analysis_type": r.analysis_type,
            "risk_score": r.risk_score,
            "verdict": r.verdict,
            "details": r.details,
            "created_at": r.created_at.isoformat()
        }
        for r in items
    ]


@router.get("/threats")
async def get_threats(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ThreatEvent)
        .where(ThreatEvent.dismissed == False)
        .order_by(ThreatEvent.created_at.desc())
        .limit(limit)
    )
    threats = result.scalars().all()
    return [
        ThreatEventResponse(
            id=t.id,
            threat_type=t.threat_type,
            severity=t.severity,
            risk_score=t.risk_score,
            title=t.title,
            description=t.description,
            source=t.source,
            indicators=t.indicators,
            action_required=t.action_required,
            dismissed=t.dismissed,
            created_at=t.created_at.isoformat()
        )
        for t in threats
    ]


@router.post("/threats/{threat_id}/dismiss")
async def dismiss_threat(threat_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ThreatEvent).where(ThreatEvent.id == threat_id))
    threat = result.scalar_one_or_none()
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")
    threat.dismissed = True
    await db.commit()
    return {"status": "dismissed"}
