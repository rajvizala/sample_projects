from datetime import datetime
from pydantic import BaseModel, Field


class EmailAnalysisRequest(BaseModel):
    sender: str = Field(..., description="Sender email address")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body content")
    headers: dict | None = Field(None, description="Raw email headers")


class URLAnalysisRequest(BaseModel):
    url: str = Field(..., description="URL to analyze")
    context: str | None = Field(None, description="Context where URL was found")


class MessageAnalysisRequest(BaseModel):
    content: str = Field(..., description="Message text content")
    sender_id: str | None = Field(None, description="Sender identifier")
    channel: str = Field(default="sms", description="Message channel: sms, chat, social")


class BatchAnalysisRequest(BaseModel):
    emails: list[EmailAnalysisRequest] = Field(default_factory=list)
    urls: list[URLAnalysisRequest] = Field(default_factory=list)
    messages: list[MessageAnalysisRequest] = Field(default_factory=list)


class ThreatIndicator(BaseModel):
    name: str
    score: float
    details: str


class ThreatResponse(BaseModel):
    id: str
    threat_type: str
    severity: str
    threat_score: float
    source_type: str
    analysis_summary: str
    recommended_action: str
    indicators: list[ThreatIndicator]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisResponse(BaseModel):
    threat_detected: bool
    threat_score: float
    severity: str
    threat_type: str
    indicators: list[ThreatIndicator]
    analysis_summary: str
    recommended_action: str
    threat_id: str | None = None
    processing_time_ms: float


class DashboardStats(BaseModel):
    total_analyses: int
    threats_detected: int
    active_threats: int
    resolved_threats: int
    avg_threat_score: float
    threat_by_type: dict[str, int]
    threat_by_severity: dict[str, int]
    detection_rate: float


class TimelineEntry(BaseModel):
    date: str
    count: int
    avg_score: float


class ThreatUpdateRequest(BaseModel):
    status: str = Field(..., description="New status: active, investigating, resolved, dismissed")
