from datetime import date, datetime
from pydantic import BaseModel, Field


class DocumentParseRequest(BaseModel):
    text: str = Field(..., description="Raw invoice or PO text to parse")
    doc_type: str = Field(default="invoice", description="Document type: invoice, po, receipt")


class ParsedLineItem(BaseModel):
    item_name: str
    quantity: int
    unit_price: float
    total: float


class DocumentParseResponse(BaseModel):
    vendor_name: str | None
    invoice_number: str | None
    po_number: str | None
    date: str | None
    due_date: str | None
    subtotal: float | None
    tax: float | None
    total: float | None
    currency: str
    payment_terms: str | None
    line_items: list[ParsedLineItem]
    confidence: float
    raw_entities: dict


class SupplierResponse(BaseModel):
    id: str
    name: str
    category: str
    country: str
    risk_score: float
    risk_level: str
    total_spend: float
    order_count: int
    avg_delivery_days: float
    on_time_rate: float
    defect_rate: float

    model_config = {"from_attributes": True}


class RiskAssessment(BaseModel):
    supplier_id: str
    supplier_name: str
    overall_risk_score: float
    risk_level: str
    factors: list["RiskFactor"]
    recommendation: str


class RiskFactor(BaseModel):
    name: str
    score: float
    weight: float
    details: str


class ForecastRequest(BaseModel):
    category: str = Field(..., description="Procurement category to forecast")
    periods: int = Field(default=12, ge=1, le=52, description="Number of periods to forecast")


class ForecastPoint(BaseModel):
    date: str
    predicted_quantity: float
    predicted_spend: float
    confidence_lower: float
    confidence_upper: float


class ForecastResponse(BaseModel):
    category: str
    model_type: str
    historical_points: int
    forecast: list[ForecastPoint]
    trend: str
    seasonality_detected: bool
    next_period_estimate: float


class SpendAnalytics(BaseModel):
    total_spend: float
    period_spend: dict[str, float]
    category_breakdown: dict[str, float]
    supplier_concentration: list[dict]
    month_over_month_change: float
    top_items: list[dict]


class AnomalyResponse(BaseModel):
    id: int
    item_name: str
    amount: float
    expected_range: str
    deviation: float
    category: str
    spend_date: str
    reason: str
    severity: str


class DashboardOverview(BaseModel):
    total_spend: float
    active_suppliers: int
    pending_orders: int
    anomalies_detected: int
    avg_risk_score: float
    spend_trend: list[dict]
    top_categories: list[dict]
    high_risk_suppliers: list[dict]
    savings_opportunity: float
