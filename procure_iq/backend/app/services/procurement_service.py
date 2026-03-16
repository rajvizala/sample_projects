"""
Core procurement service orchestrating all business logic.
"""

from datetime import date, timedelta
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.models.procurement import Supplier, PurchaseOrder, SpendRecord, ForecastResult
from app.schemas.procurement import (
    SpendAnalytics,
    DashboardOverview,
    DocumentParseRequest,
    DocumentParseResponse,
    ForecastRequest,
    ForecastResponse,
    RiskAssessment,
    AnomalyResponse,
)
from app.ml.document_parser import parse_document
from app.ml.forecaster import forecast_demand
from app.ml.risk_scorer import score_supplier_risk
from app.ml.anomaly_detector import detect_spending_anomalies


class ProcurementService:

    def parse_document(self, request: DocumentParseRequest) -> DocumentParseResponse:
        return parse_document(request.text, request.doc_type)

    def get_suppliers(self, db: Session, category: str | None = None) -> list[Supplier]:
        query = db.query(Supplier)
        if category:
            query = query.filter(Supplier.category == category)
        return query.order_by(desc(Supplier.total_spend)).all()

    def get_supplier(self, db: Session, supplier_id: str) -> Supplier | None:
        return db.query(Supplier).filter(Supplier.id == supplier_id).first()

    def get_supplier_risk(self, db: Session, supplier_id: str) -> RiskAssessment | None:
        supplier = self.get_supplier(db, supplier_id)
        if not supplier:
            return None

        portfolio_spend = db.query(func.sum(Supplier.total_spend)).scalar() or 0

        meta = supplier.metadata_json or {}
        return score_supplier_risk(
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            on_time_rate=supplier.on_time_rate,
            defect_rate=supplier.defect_rate,
            avg_delivery_days=supplier.avg_delivery_days,
            expected_delivery_days=10.0,
            total_spend=supplier.total_spend,
            portfolio_total_spend=portfolio_spend,
            order_count=supplier.order_count,
            country=supplier.country,
            years_in_business=meta.get("years_in_business", 5),
        )

    def generate_forecast(self, db: Session, request: ForecastRequest) -> ForecastResponse:
        records = (
            db.query(SpendRecord)
            .filter(SpendRecord.category == request.category)
            .order_by(SpendRecord.spend_date)
            .all()
        )

        monthly: dict[str, dict] = {}
        for r in records:
            month_key = r.spend_date.strftime("%Y-%m")
            if month_key not in monthly:
                monthly[month_key] = {"date": r.spend_date.replace(day=1), "qty": 0, "amt": 0.0}
            monthly[month_key]["qty"] += r.quantity
            monthly[month_key]["amt"] += r.amount

        sorted_months = sorted(monthly.values(), key=lambda x: x["date"])
        dates = [m["date"] for m in sorted_months]
        quantities = [m["qty"] for m in sorted_months]
        amounts = [m["amt"] for m in sorted_months]

        return forecast_demand(
            dates=dates,
            quantities=quantities,
            amounts=amounts,
            periods=request.periods,
            category=request.category,
        )

    def get_spend_analytics(self, db: Session, days: int = 365) -> SpendAnalytics:
        cutoff = date.today() - timedelta(days=days)
        records = db.query(SpendRecord).filter(SpendRecord.spend_date >= cutoff).all()

        total_spend = sum(r.amount for r in records)

        period_spend: dict[str, float] = {}
        for r in records:
            month = r.spend_date.strftime("%Y-%m")
            period_spend[month] = period_spend.get(month, 0) + r.amount

        category_breakdown: dict[str, float] = {}
        for r in records:
            category_breakdown[r.category] = category_breakdown.get(r.category, 0) + r.amount

        supplier_spend: dict[str, float] = {}
        for r in records:
            supplier_spend[r.supplier_id] = supplier_spend.get(r.supplier_id, 0) + r.amount
        suppliers = db.query(Supplier).all()
        supplier_map = {s.id: s.name for s in suppliers}
        supplier_concentration = sorted(
            [{"name": supplier_map.get(sid, sid), "spend": amt, "share": round(amt / max(total_spend, 1) * 100, 1)}
             for sid, amt in supplier_spend.items()],
            key=lambda x: x["spend"],
            reverse=True,
        )[:10]

        months = sorted(period_spend.keys())
        if len(months) >= 2:
            last_month = period_spend[months[-1]]
            prev_month = period_spend[months[-2]]
            mom_change = ((last_month - prev_month) / max(prev_month, 1)) * 100
        else:
            mom_change = 0.0

        item_spend: dict[str, dict] = {}
        for r in records:
            if r.item_name not in item_spend:
                item_spend[r.item_name] = {"name": r.item_name, "total": 0, "count": 0}
            item_spend[r.item_name]["total"] += r.amount
            item_spend[r.item_name]["count"] += 1
        top_items = sorted(item_spend.values(), key=lambda x: x["total"], reverse=True)[:10]

        return SpendAnalytics(
            total_spend=round(total_spend, 2),
            period_spend={k: round(v, 2) for k, v in sorted(period_spend.items())},
            category_breakdown={k: round(v, 2) for k, v in category_breakdown.items()},
            supplier_concentration=supplier_concentration,
            month_over_month_change=round(mom_change, 1),
            top_items=top_items,
        )

    def get_anomalies(self, db: Session, days: int = 365) -> list[AnomalyResponse]:
        cutoff = date.today() - timedelta(days=days)
        records = db.query(SpendRecord).filter(SpendRecord.spend_date >= cutoff).all()

        record_dicts = [
            {
                "id": r.id,
                "item_name": r.item_name,
                "amount": r.amount,
                "unit_price": r.unit_price,
                "quantity": r.quantity,
                "category": r.category,
                "spend_date": r.spend_date,
            }
            for r in records
        ]

        return detect_spending_anomalies(record_dicts)

    def get_dashboard_overview(self, db: Session) -> DashboardOverview:
        total_spend = db.query(func.sum(Supplier.total_spend)).scalar() or 0
        active_suppliers = db.query(Supplier).count()
        pending_orders = db.query(PurchaseOrder).filter(PurchaseOrder.status == "pending").count()

        cutoff = date.today() - timedelta(days=90)
        recent_records = db.query(SpendRecord).filter(SpendRecord.spend_date >= cutoff).all()
        record_dicts = [
            {
                "id": r.id, "item_name": r.item_name, "amount": r.amount,
                "unit_price": r.unit_price, "quantity": r.quantity,
                "category": r.category, "spend_date": r.spend_date,
            }
            for r in recent_records
        ]
        anomalies = detect_spending_anomalies(record_dicts) if len(record_dicts) >= 5 else []

        avg_risk = db.query(func.avg(Supplier.risk_score)).scalar() or 50

        spend_by_month: dict[str, float] = {}
        for r in recent_records:
            m = r.spend_date.strftime("%Y-%m")
            spend_by_month[m] = spend_by_month.get(m, 0) + r.amount
        spend_trend = [{"month": k, "spend": round(v, 2)} for k, v in sorted(spend_by_month.items())]

        cat_spend: dict[str, float] = {}
        for r in recent_records:
            cat_spend[r.category] = cat_spend.get(r.category, 0) + r.amount
        top_categories = sorted(
            [{"name": k, "spend": round(v, 2)} for k, v in cat_spend.items()],
            key=lambda x: x["spend"], reverse=True,
        )[:5]

        high_risk = (
            db.query(Supplier)
            .filter(Supplier.risk_score >= 55)
            .order_by(desc(Supplier.risk_score))
            .limit(5)
            .all()
        )
        high_risk_list = [
            {"name": s.name, "risk_score": s.risk_score, "category": s.category}
            for s in high_risk
        ]

        savings = total_spend * 0.05

        return DashboardOverview(
            total_spend=round(total_spend, 2),
            active_suppliers=active_suppliers,
            pending_orders=pending_orders,
            anomalies_detected=len(anomalies),
            avg_risk_score=round(float(avg_risk), 1),
            spend_trend=spend_trend,
            top_categories=top_categories,
            high_risk_suppliers=high_risk_list,
            savings_opportunity=round(savings, 2),
        )


_service: ProcurementService | None = None


def get_procurement_service() -> ProcurementService:
    global _service
    if _service is None:
        _service = ProcurementService()
    return _service
