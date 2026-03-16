"""
API routes for ProcureIQ procurement intelligence platform.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.procurement import (
    DocumentParseRequest,
    DocumentParseResponse,
    SupplierResponse,
    RiskAssessment,
    ForecastRequest,
    ForecastResponse,
    SpendAnalytics,
    AnomalyResponse,
    DashboardOverview,
)
from app.services.procurement_service import get_procurement_service

router = APIRouter(prefix="/api/v1")


@router.post("/documents/parse", response_model=DocumentParseResponse, tags=["Documents"])
def parse_document(request: DocumentParseRequest):
    """Parse unstructured invoice/PO text into structured procurement data."""
    service = get_procurement_service()
    return service.parse_document(request)


@router.get("/suppliers", tags=["Suppliers"])
def list_suppliers(
    category: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """List all suppliers with optional category filter."""
    service = get_procurement_service()
    suppliers = service.get_suppliers(db, category)
    return {
        "total": len(suppliers),
        "suppliers": [SupplierResponse.model_validate(s) for s in suppliers],
    }


@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse, tags=["Suppliers"])
def get_supplier(supplier_id: str, db: Session = Depends(get_db)):
    """Get detailed supplier information."""
    service = get_procurement_service()
    supplier = service.get_supplier(db, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return SupplierResponse.model_validate(supplier)


@router.get("/suppliers/{supplier_id}/risk", response_model=RiskAssessment, tags=["Suppliers"])
def get_supplier_risk(supplier_id: str, db: Session = Depends(get_db)):
    """Get detailed risk assessment for a supplier."""
    service = get_procurement_service()
    risk = service.get_supplier_risk(db, supplier_id)
    if not risk:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return risk


@router.post("/forecast/generate", response_model=ForecastResponse, tags=["Forecasting"])
def generate_forecast(request: ForecastRequest, db: Session = Depends(get_db)):
    """Generate demand forecast for a procurement category."""
    service = get_procurement_service()
    return service.generate_forecast(db, request)


@router.get("/analytics/spend", response_model=SpendAnalytics, tags=["Analytics"])
def spend_analytics(
    days: int = Query(365, ge=30, le=1095),
    db: Session = Depends(get_db),
):
    """Get spend analytics and breakdown."""
    service = get_procurement_service()
    return service.get_spend_analytics(db, days)


@router.get("/analytics/anomalies", tags=["Analytics"])
def spending_anomalies(
    days: int = Query(365, ge=30, le=1095),
    db: Session = Depends(get_db),
):
    """Detect spending anomalies using ML."""
    service = get_procurement_service()
    anomalies = service.get_anomalies(db, days)
    return {"total": len(anomalies), "anomalies": anomalies}


@router.get("/analytics/savings", tags=["Analytics"])
def savings_opportunities(db: Session = Depends(get_db)):
    """Identify savings opportunities across procurement."""
    service = get_procurement_service()
    analytics = service.get_spend_analytics(db, 365)

    opportunities = []
    for item in analytics.top_items[:5]:
        potential = item["total"] * 0.08
        opportunities.append({
            "item": item["name"],
            "current_spend": round(item["total"], 2),
            "potential_savings": round(potential, 2),
            "strategy": "Volume consolidation and competitive bidding",
        })

    for supplier in analytics.supplier_concentration[:3]:
        if supplier["share"] > 20:
            opportunities.append({
                "item": f"Diversify from {supplier['name']}",
                "current_spend": round(supplier["spend"], 2),
                "potential_savings": round(supplier["spend"] * 0.05, 2),
                "strategy": "Supplier diversification to reduce concentration risk and improve pricing leverage",
            })

    total_potential = sum(o["potential_savings"] for o in opportunities)
    return {
        "total_potential_savings": round(total_potential, 2),
        "opportunities": opportunities,
    }


@router.get("/dashboard/overview", response_model=DashboardOverview, tags=["Dashboard"])
def dashboard_overview(db: Session = Depends(get_db)):
    """Get dashboard summary metrics."""
    service = get_procurement_service()
    return service.get_dashboard_overview(db)
