"""
Spend anomaly detection using statistical methods and Isolation Forest.
Identifies unusual spending patterns, price spikes, potential duplicate
payments, and budget deviations.
"""

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from datetime import date

from app.schemas.procurement import AnomalyResponse


def detect_spending_anomalies(
    records: list[dict],
    contamination: float = 0.05,
) -> list[AnomalyResponse]:
    """
    Detect anomalies in spending records using a combination of
    statistical Z-score analysis and Isolation Forest.

    Each record should have: id, item_name, amount, unit_price, quantity,
    category, spend_date
    """
    if len(records) < 5:
        return []

    anomalies = []
    anomalies.extend(_zscore_anomalies(records))
    anomalies.extend(_isolation_forest_anomalies(records, contamination))
    anomalies.extend(_duplicate_detection(records))
    anomalies.extend(_price_spike_detection(records))

    seen_ids = set()
    unique = []
    for a in anomalies:
        if a.id not in seen_ids:
            seen_ids.add(a.id)
            unique.append(a)

    return sorted(unique, key=lambda x: x.deviation, reverse=True)


def _zscore_anomalies(records: list[dict]) -> list[AnomalyResponse]:
    """Flag records with Z-score > 2.5 in amount or unit_price."""
    anomalies = []
    by_category: dict[str, list[dict]] = {}
    for r in records:
        by_category.setdefault(r["category"], []).append(r)

    for category, cat_records in by_category.items():
        amounts = np.array([r["amount"] for r in cat_records])
        if len(amounts) < 3:
            continue

        mean_amt = np.mean(amounts)
        std_amt = np.std(amounts)
        if std_amt == 0:
            continue

        for r in cat_records:
            z = abs(r["amount"] - mean_amt) / std_amt
            if z > 2.5:
                anomalies.append(AnomalyResponse(
                    id=r["id"],
                    item_name=r["item_name"],
                    amount=r["amount"],
                    expected_range=f"${mean_amt - 2*std_amt:.2f} - ${mean_amt + 2*std_amt:.2f}",
                    deviation=round(float(z), 2),
                    category=r["category"],
                    spend_date=str(r["spend_date"]),
                    reason=f"Amount is {z:.1f} standard deviations from category mean (${mean_amt:.2f})",
                    severity="high" if z > 3.5 else "medium",
                ))

    return anomalies


def _isolation_forest_anomalies(records: list[dict], contamination: float) -> list[AnomalyResponse]:
    """Use Isolation Forest for multivariate anomaly detection."""
    features = []
    for r in records:
        features.append([
            r["amount"],
            r["unit_price"],
            r["quantity"],
        ])

    X = np.array(features)
    if len(X) < 10:
        return []

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = IsolationForest(
        contamination=contamination,
        n_estimators=100,
        random_state=42,
    )
    predictions = model.fit_predict(X_scaled)
    scores = model.decision_function(X_scaled)

    anomalies = []
    for i, (pred, score) in enumerate(zip(predictions, scores)):
        if pred == -1:
            r = records[i]
            deviation = round(float(-score), 2)
            anomalies.append(AnomalyResponse(
                id=r["id"],
                item_name=r["item_name"],
                amount=r["amount"],
                expected_range="multivariate analysis",
                deviation=deviation,
                category=r["category"],
                spend_date=str(r["spend_date"]),
                reason=f"Multivariate outlier detected (amount=${r['amount']:.2f}, qty={r['quantity']}, unit=${r['unit_price']:.2f})",
                severity="high" if deviation > 0.3 else "medium",
            ))

    return anomalies


def _duplicate_detection(records: list[dict]) -> list[AnomalyResponse]:
    """Detect potential duplicate payments."""
    anomalies = []
    seen: dict[str, list[dict]] = {}

    for r in records:
        key = f"{r.get('item_name', '')}_{r['amount']:.2f}"
        seen.setdefault(key, []).append(r)

    for key, dupes in seen.items():
        if len(dupes) < 2:
            continue

        dates = sorted([r["spend_date"] for r in dupes])
        for i in range(1, len(dates)):
            d1 = dates[i - 1] if isinstance(dates[i - 1], date) else date.fromisoformat(str(dates[i - 1]))
            d2 = dates[i] if isinstance(dates[i], date) else date.fromisoformat(str(dates[i]))
            if (d2 - d1).days <= 7:
                r = dupes[i]
                anomalies.append(AnomalyResponse(
                    id=r["id"],
                    item_name=r["item_name"],
                    amount=r["amount"],
                    expected_range="unique payment",
                    deviation=3.0,
                    category=r["category"],
                    spend_date=str(r["spend_date"]),
                    reason=f"Potential duplicate: same item and amount within 7 days",
                    severity="high",
                ))

    return anomalies


def _price_spike_detection(records: list[dict]) -> list[AnomalyResponse]:
    """Detect sudden price spikes for specific items."""
    anomalies = []
    by_item: dict[str, list[dict]] = {}

    for r in records:
        by_item.setdefault(r["item_name"], []).append(r)

    for item, item_records in by_item.items():
        if len(item_records) < 3:
            continue

        sorted_records = sorted(item_records, key=lambda x: str(x["spend_date"]))
        prices = [r["unit_price"] for r in sorted_records]

        for i in range(2, len(prices)):
            recent_avg = np.mean(prices[max(0, i - 3):i])
            if recent_avg > 0 and prices[i] > recent_avg * 1.5:
                r = sorted_records[i]
                spike = (prices[i] - recent_avg) / recent_avg * 100
                anomalies.append(AnomalyResponse(
                    id=r["id"],
                    item_name=r["item_name"],
                    amount=r["amount"],
                    expected_range=f"~${recent_avg:.2f}/unit",
                    deviation=round(spike / 50, 2),
                    category=r["category"],
                    spend_date=str(r["spend_date"]),
                    reason=f"Price spike: ${r['unit_price']:.2f}/unit vs ${recent_avg:.2f} avg ({spike:.0f}% increase)",
                    severity="high" if spike > 100 else "medium",
                ))

    return anomalies
