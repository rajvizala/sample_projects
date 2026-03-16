import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Text, DateTime, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Threat(Base):
    __tablename__ = "threats"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    threat_type: Mapped[str] = mapped_column(String(50), index=True)
    severity: Mapped[str] = mapped_column(String(20), index=True)
    threat_score: Mapped[float] = mapped_column(Float)
    source_type: Mapped[str] = mapped_column(String(30))
    source_content: Mapped[str] = mapped_column(Text)
    analysis_summary: Mapped[str] = mapped_column(Text)
    recommended_action: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)

    phishing_score: Mapped[float] = mapped_column(Float, default=0.0)
    anomaly_score: Mapped[float] = mapped_column(Float, default=0.0)
    ai_generated_score: Mapped[float] = mapped_column(Float, default=0.0)
    url_threat_score: Mapped[float] = mapped_column(Float, default=0.0)

    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class AnalysisLog(Base):
    __tablename__ = "analysis_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    input_type: Mapped[str] = mapped_column(String(30))
    input_hash: Mapped[str] = mapped_column(String(64), index=True)
    threat_detected: Mapped[int] = mapped_column(Integer, default=0)
    processing_time_ms: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
