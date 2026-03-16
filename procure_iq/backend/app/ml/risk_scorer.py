"""
Multi-factor supplier risk scoring engine.
Combines delivery performance, financial indicators, concentration risk,
compliance signals, and market factors into a composite risk assessment.
"""

import numpy as np
from app.schemas.procurement import RiskAssessment, RiskFactor


RISK_WEIGHTS = {
    "delivery_performance": 0.25,
    "quality_metrics": 0.20,
    "financial_stability": 0.20,
    "concentration_risk": 0.15,
    "compliance": 0.10,
    "market_volatility": 0.10,
}


def score_supplier_risk(
    supplier_id: str,
    supplier_name: str,
    on_time_rate: float,
    defect_rate: float,
    avg_delivery_days: float,
    expected_delivery_days: float,
    total_spend: float,
    portfolio_total_spend: float,
    order_count: int,
    country: str,
    years_in_business: int = 5,
    has_certifications: bool = True,
    market_price_volatility: float = 0.1,
) -> RiskAssessment:
    """Calculate comprehensive supplier risk assessment."""
    factors = []

    delivery_score = _score_delivery(on_time_rate, avg_delivery_days, expected_delivery_days)
    factors.append(RiskFactor(
        name="Delivery Performance",
        score=round(delivery_score, 1),
        weight=RISK_WEIGHTS["delivery_performance"],
        details=_delivery_details(on_time_rate, avg_delivery_days, expected_delivery_days),
    ))

    quality_score = _score_quality(defect_rate)
    factors.append(RiskFactor(
        name="Quality Metrics",
        score=round(quality_score, 1),
        weight=RISK_WEIGHTS["quality_metrics"],
        details=f"Defect rate: {defect_rate:.1%}. {'Acceptable' if defect_rate < 0.03 else 'Above threshold'}.",
    ))

    financial_score = _score_financial_stability(order_count, years_in_business, total_spend)
    factors.append(RiskFactor(
        name="Financial Stability",
        score=round(financial_score, 1),
        weight=RISK_WEIGHTS["financial_stability"],
        details=f"Track record: {order_count} orders over {years_in_business} years.",
    ))

    concentration_score = _score_concentration(total_spend, portfolio_total_spend)
    factors.append(RiskFactor(
        name="Concentration Risk",
        score=round(concentration_score, 1),
        weight=RISK_WEIGHTS["concentration_risk"],
        details=f"Supplier represents {total_spend/max(portfolio_total_spend,1):.1%} of total spend.",
    ))

    compliance_score = _score_compliance(has_certifications, country)
    factors.append(RiskFactor(
        name="Compliance",
        score=round(compliance_score, 1),
        weight=RISK_WEIGHTS["compliance"],
        details=f"{'Certified' if has_certifications else 'No certifications'}. Region: {country}.",
    ))

    market_score = _score_market_volatility(market_price_volatility)
    factors.append(RiskFactor(
        name="Market Volatility",
        score=round(market_score, 1),
        weight=RISK_WEIGHTS["market_volatility"],
        details=f"Price volatility index: {market_price_volatility:.2f}.",
    ))

    overall = sum(f.score * f.weight for f in factors)

    if overall >= 75:
        level = "critical"
        recommendation = (
            "Immediate action required. Consider qualifying alternative suppliers and "
            "establishing contingency plans. Review contract terms for risk mitigation."
        )
    elif overall >= 55:
        level = "high"
        recommendation = (
            "Closely monitor this supplier. Begin parallel qualification of backup suppliers. "
            "Schedule performance review meeting."
        )
    elif overall >= 35:
        level = "medium"
        recommendation = (
            "Standard monitoring. Continue regular performance reviews and maintain "
            "existing risk mitigation measures."
        )
    else:
        level = "low"
        recommendation = (
            "Healthy supplier relationship. Consider for strategic partnership or "
            "volume consolidation opportunities."
        )

    return RiskAssessment(
        supplier_id=supplier_id,
        supplier_name=supplier_name,
        overall_risk_score=round(overall, 1),
        risk_level=level,
        factors=factors,
        recommendation=recommendation,
    )


def _score_delivery(on_time_rate: float, avg_days: float, expected_days: float) -> float:
    late_penalty = max(0, 1 - on_time_rate) * 60
    delay_ratio = max(0, avg_days - expected_days) / max(expected_days, 1)
    delay_penalty = min(delay_ratio * 40, 40)
    return min(late_penalty + delay_penalty, 100)


def _delivery_details(on_time_rate: float, avg_days: float, expected_days: float) -> str:
    parts = [f"On-time rate: {on_time_rate:.0%}"]
    if avg_days > expected_days:
        parts.append(f"avg {avg_days:.1f} days vs {expected_days:.0f} expected")
    return ". ".join(parts) + "."


def _score_quality(defect_rate: float) -> float:
    if defect_rate <= 0.01:
        return 10
    elif defect_rate <= 0.03:
        return 30
    elif defect_rate <= 0.05:
        return 55
    elif defect_rate <= 0.10:
        return 75
    else:
        return 95


def _score_financial_stability(order_count: int, years: int, total_spend: float) -> float:
    score = 50.0
    if order_count < 5:
        score += 25
    elif order_count < 20:
        score += 10
    else:
        score -= 15

    if years < 2:
        score += 20
    elif years > 5:
        score -= 15

    return np.clip(score, 0, 100)


def _score_concentration(supplier_spend: float, total_spend: float) -> float:
    if total_spend == 0:
        return 50
    ratio = supplier_spend / total_spend
    if ratio > 0.30:
        return 90
    elif ratio > 0.20:
        return 70
    elif ratio > 0.10:
        return 45
    else:
        return 20


def _score_compliance(has_certs: bool, country: str) -> float:
    score = 30.0 if has_certs else 60.0
    high_risk_regions = {"CN", "RU", "IN", "BR", "MX"}
    if country.upper() in high_risk_regions or len(country) > 2 and country.upper()[:2] in high_risk_regions:
        score += 15
    return min(score, 100)


def _score_market_volatility(volatility: float) -> float:
    if volatility < 0.05:
        return 15
    elif volatility < 0.15:
        return 40
    elif volatility < 0.30:
        return 65
    else:
        return 85
