"""
API routes for ThreatLens threat analysis and management.
"""

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.threat import Threat, AnalysisLog
from app.schemas.threat import (
    EmailAnalysisRequest,
    URLAnalysisRequest,
    MessageAnalysisRequest,
    BatchAnalysisRequest,
    AnalysisResponse,
    ThreatResponse,
    ThreatIndicator,
    DashboardStats,
    TimelineEntry,
    ThreatUpdateRequest,
)
from app.services.analysis import get_analysis_service

router = APIRouter(prefix="/api/v1")


@router.post("/analyze/email", response_model=AnalysisResponse, tags=["Analysis"])
def analyze_email(request: EmailAnalysisRequest, db: Session = Depends(get_db)):
    """Analyze an email for phishing, scam, and AI-generated content threats."""
    service = get_analysis_service()
    return service.analyze_email(request, db)


@router.post("/analyze/url", response_model=AnalysisResponse, tags=["Analysis"])
def analyze_url(request: URLAnalysisRequest, db: Session = Depends(get_db)):
    """Analyze a URL for phishing and malicious content."""
    service = get_analysis_service()
    return service.analyze_url(request, db)


@router.post("/analyze/message", response_model=AnalysisResponse, tags=["Analysis"])
def analyze_message(request: MessageAnalysisRequest, db: Session = Depends(get_db)):
    """Analyze a text message for scam, phishing, and AI-generated content."""
    service = get_analysis_service()
    return service.analyze_message(request, db)


@router.post("/analyze/batch", tags=["Analysis"])
def analyze_batch(request: BatchAnalysisRequest, db: Session = Depends(get_db)):
    """Batch analysis of multiple emails, URLs, and messages."""
    service = get_analysis_service()
    results = {"emails": [], "urls": [], "messages": []}

    for email in request.emails:
        results["emails"].append(service.analyze_email(email, db))
    for url in request.urls:
        results["urls"].append(service.analyze_url(url, db))
    for msg in request.messages:
        results["messages"].append(service.analyze_message(msg, db))

    total = len(results["emails"]) + len(results["urls"]) + len(results["messages"])
    threats = sum(
        1 for r in [*results["emails"], *results["urls"], *results["messages"]]
        if r.threat_detected
    )
    return {
        "total_analyzed": total,
        "threats_found": threats,
        "results": results,
    }


@router.get("/threats", tags=["Threats"])
def list_threats(
    status: str | None = Query(None, description="Filter by status"),
    severity: str | None = Query(None, description="Filter by severity"),
    threat_type: str | None = Query(None, description="Filter by threat type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List detected threats with optional filters."""
    query = db.query(Threat)
    if status:
        query = query.filter(Threat.status == status)
    if severity:
        query = query.filter(Threat.severity == severity)
    if threat_type:
        query = query.filter(Threat.threat_type == threat_type)

    total = query.count()
    threats = query.order_by(desc(Threat.created_at)).offset(offset).limit(limit).all()

    return {
        "total": total,
        "threats": [
            ThreatResponse(
                id=t.id,
                threat_type=t.threat_type,
                severity=t.severity,
                threat_score=t.threat_score,
                source_type=t.source_type,
                analysis_summary=t.analysis_summary,
                recommended_action=t.recommended_action,
                indicators=_reconstruct_indicators(t),
                status=t.status,
                created_at=t.created_at,
            )
            for t in threats
        ],
    }


@router.get("/threats/{threat_id}", response_model=ThreatResponse, tags=["Threats"])
def get_threat(threat_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific threat."""
    threat = db.query(Threat).filter(Threat.id == threat_id).first()
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")

    return ThreatResponse(
        id=threat.id,
        threat_type=threat.threat_type,
        severity=threat.severity,
        threat_score=threat.threat_score,
        source_type=threat.source_type,
        analysis_summary=threat.analysis_summary,
        recommended_action=threat.recommended_action,
        indicators=_reconstruct_indicators(threat),
        status=threat.status,
        created_at=threat.created_at,
    )


@router.patch("/threats/{threat_id}", tags=["Threats"])
def update_threat(threat_id: str, request: ThreatUpdateRequest, db: Session = Depends(get_db)):
    """Update threat status (active, investigating, resolved, dismissed)."""
    threat = db.query(Threat).filter(Threat.id == threat_id).first()
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")

    valid_statuses = {"active", "investigating", "resolved", "dismissed"}
    if request.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    threat.status = request.status
    if request.status == "resolved":
        threat.resolved_at = datetime.now(timezone.utc)
    db.commit()
    return {"id": threat_id, "status": request.status}


@router.get("/dashboard/stats", response_model=DashboardStats, tags=["Dashboard"])
def dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics for the threat overview."""
    total_analyses = db.query(AnalysisLog).count()
    threats_detected = db.query(AnalysisLog).filter(AnalysisLog.threat_detected == 1).count()
    active_threats = db.query(Threat).filter(Threat.status == "active").count()
    resolved_threats = db.query(Threat).filter(Threat.status == "resolved").count()

    avg_score_result = db.query(func.avg(Threat.threat_score)).scalar()
    avg_score = float(avg_score_result) if avg_score_result else 0.0

    type_counts = (
        db.query(Threat.threat_type, func.count(Threat.id))
        .group_by(Threat.threat_type)
        .all()
    )
    severity_counts = (
        db.query(Threat.severity, func.count(Threat.id))
        .group_by(Threat.severity)
        .all()
    )

    return DashboardStats(
        total_analyses=total_analyses,
        threats_detected=threats_detected,
        active_threats=active_threats,
        resolved_threats=resolved_threats,
        avg_threat_score=round(avg_score, 1),
        threat_by_type={t: c for t, c in type_counts},
        threat_by_severity={s: c for s, c in severity_counts},
        detection_rate=round(threats_detected / max(total_analyses, 1) * 100, 1),
    )


@router.get("/dashboard/timeline", tags=["Dashboard"])
def dashboard_timeline(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get threat detection timeline for charts."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    threats = (
        db.query(Threat)
        .filter(Threat.created_at >= cutoff)
        .order_by(Threat.created_at)
        .all()
    )

    daily: dict[str, list] = {}
    for t in threats:
        day = t.created_at.strftime("%Y-%m-%d")
        daily.setdefault(day, []).append(t.threat_score)

    return [
        TimelineEntry(
            date=day,
            count=len(scores),
            avg_score=round(sum(scores) / len(scores), 1),
        )
        for day, scores in sorted(daily.items())
    ]


def _reconstruct_indicators(threat: Threat) -> list[ThreatIndicator]:
    """Reconstruct threat indicators from stored scores."""
    indicators = []
    if threat.phishing_score > 0:
        indicators.append(ThreatIndicator(
            name="Phishing Content",
            score=round(threat.phishing_score * 100, 1),
            details="Phishing indicators detected in content",
        ))
    if threat.url_threat_score > 0:
        indicators.append(ThreatIndicator(
            name="Malicious URL",
            score=round(threat.url_threat_score * 100, 1),
            details="Suspicious URL characteristics detected",
        ))
    if threat.anomaly_score > 0:
        indicators.append(ThreatIndicator(
            name="Behavioral Anomaly",
            score=round(threat.anomaly_score * 100, 1),
            details="Communication pattern deviation detected",
        ))
    if threat.ai_generated_score > 0:
        indicators.append(ThreatIndicator(
            name="AI-Generated Content",
            score=round(threat.ai_generated_score * 100, 1),
            details="Content may be AI-generated",
        ))
    return indicators
