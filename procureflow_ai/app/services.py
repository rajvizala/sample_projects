from __future__ import annotations

from collections import defaultdict
from statistics import mean

import numpy as np

from . import models


def _split_csv(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(',') if item.strip()]


def serialize_supplier(supplier: models.Supplier) -> dict:
    return {
        'id': supplier.id,
        'name': supplier.name,
        'category': supplier.category,
        'lead_time_days': supplier.lead_time_days,
        'on_time_rate': supplier.on_time_rate,
        'quality_score': supplier.quality_score,
        'risk_score': supplier.risk_score,
        'certifications': _split_csv(supplier.certifications),
        'preferred': bool(supplier.preferred),
    }


def serialize_requisition(requisition: models.Requisition) -> dict:
    return {
        'id': requisition.id,
        'title': requisition.title,
        'category': requisition.category,
        'quantity': requisition.quantity,
        'needed_by': requisition.needed_by.isoformat(),
        'priority': requisition.priority,
        'required_certifications': _split_csv(requisition.required_certifications),
        'created_at': requisition.created_at.isoformat(),
    }


def serialize_quote(quote: models.Quote) -> dict:
    return {
        'id': quote.id,
        'requisition_id': quote.requisition_id,
        'supplier_id': quote.supplier_id,
        'supplier_name': quote.supplier.name,
        'unit_price': quote.unit_price,
        'available_qty': quote.available_qty,
        'lead_time_days': quote.lead_time_days,
        'note': quote.note,
    }


def recommend_quote(requisition: models.Requisition, quotes: list[models.Quote]) -> dict | None:
    if not quotes:
        return None

    best = None
    rationale = None
    for quote in quotes:
        supplier = quote.supplier
        certs = set(_split_csv(supplier.certifications))
        required = set(_split_csv(requisition.required_certifications))
        cert_match = required.issubset(certs)
        availability_ratio = min(quote.available_qty / requisition.quantity, 1.0)
        score = (
            max(0, 35 - quote.unit_price / 4)
            + max(0, 20 - quote.lead_time_days)
            + supplier.on_time_rate * 18
            + supplier.quality_score * 16
            + (8 if cert_match else -12)
            + availability_ratio * 10
            + (4 if supplier.preferred else 0)
            - supplier.risk_score * 14
        )
        if best is None or score > best:
            best = score
            rationale = {
                'supplier': supplier.name,
                'score': round(score, 1),
                'unit_price': quote.unit_price,
                'lead_time_days': quote.lead_time_days,
                'why': [
                    f"On-time rate {supplier.on_time_rate:.0%}",
                    f"Quality score {supplier.quality_score:.2f}",
                    'Certification match' if cert_match else 'Certification gap',
                    f"Risk score {supplier.risk_score:.2f}",
                ],
            }
    return rationale


def forecast_demand(signals: list[models.DemandSignal]) -> list[dict]:
    grouped = defaultdict(list)
    for signal in signals:
        grouped[signal.category].append(signal)
    forecasts = []
    for category, items in grouped.items():
        ordered = sorted(items, key=lambda item: item.week_index)
        x = np.array([item.week_index for item in ordered])
        y = np.array([item.units for item in ordered])
        if len(ordered) >= 2:
            slope, intercept = np.polyfit(x, y, 1)
            next_week = int(round(slope * (max(x) + 1) + intercept))
        else:
            next_week = int(y[-1])
        forecasts.append({
            'category': category,
            'last_observed': int(y[-1]),
            'next_week_forecast': max(0, next_week),
            'trend': 'up' if next_week > y[-1] else 'down' if next_week < y[-1] else 'flat',
        })
    return sorted(forecasts, key=lambda item: item['category'])


def price_anomalies(quotes: list[models.Quote]) -> list[dict]:
    category_prices = defaultdict(list)
    for quote in quotes:
        category_prices[quote.requisition.category].append(quote.unit_price)
    anomalies = []
    for quote in quotes:
        prices = category_prices[quote.requisition.category]
        avg_price = mean(prices)
        if quote.unit_price > avg_price * 1.18:
            anomalies.append({
                'supplier': quote.supplier.name,
                'category': quote.requisition.category,
                'unit_price': quote.unit_price,
                'benchmark': round(avg_price, 2),
                'message': 'Quote is materially above category average and should be renegotiated.',
            })
    return anomalies
