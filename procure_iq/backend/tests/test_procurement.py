"""Tests for ProcureIQ ML pipeline components."""

import pytest
import numpy as np
from datetime import date, timedelta

from app.ml.document_parser import parse_document
from app.ml.forecaster import (
    exponential_smoothing,
    double_exponential_smoothing,
    detect_seasonality,
    forecast_demand,
)
from app.ml.risk_scorer import score_supplier_risk
from app.ml.anomaly_detector import detect_spending_anomalies


class TestDocumentParser:
    def test_parse_invoice(self):
        text = """INVOICE
From: Apex Manufacturing Co.
Invoice #: INV-2024-0847
Date: January 15, 2024
Payment Terms: Net 30

Steel Plates (Grade A)             50      185.00    9250.00
Aluminum Ingots                    30      120.00    3600.00

Subtotal: $12,850.00
Tax: $1,028.00
Total: $13,878.00"""

        result = parse_document(text, "invoice")
        assert result.vendor_name is not None
        assert result.invoice_number is not None
        assert result.total is not None
        assert len(result.line_items) >= 1

    def test_parse_extracts_amounts(self):
        text = "Subtotal: $500.00\nTax: $40.00\nTotal: $540.00"
        result = parse_document(text)
        assert result.subtotal == 500.00
        assert result.tax == 40.00
        assert result.total == 540.00

    def test_parse_payment_terms(self):
        text = "Invoice from Vendor\nPayment Terms: Net 30\nTotal: $100"
        result = parse_document(text)
        assert result.payment_terms is not None
        assert "net" in result.payment_terms.lower()


class TestForecaster:
    def test_exponential_smoothing(self):
        series = np.array([10, 12, 15, 13, 17, 20])
        result = exponential_smoothing(series, alpha=0.3)
        assert len(result) == len(series)
        assert result[0] == series[0]

    def test_double_exponential_smoothing(self):
        series = np.array([10, 12, 15, 18, 22, 25, 30])
        forecast = double_exponential_smoothing(series, periods=6)
        assert len(forecast) == 6
        assert all(f > 0 for f in forecast)

    def test_detect_seasonality_none(self):
        series = np.array([1, 2, 3, 4, 5])
        result = detect_seasonality(series)
        assert result is None

    def test_forecast_demand(self):
        dates = [date.today() - timedelta(days=30 * i) for i in range(12, 0, -1)]
        quantities = [100 + i * 5 + np.random.randint(-10, 10) for i in range(12)]
        amounts = [q * 15.0 for q in quantities]

        result = forecast_demand(dates, quantities, amounts, periods=6, category="Test")
        assert result.category == "Test"
        assert len(result.forecast) == 6
        assert result.historical_points == 12
        assert result.trend in ("increasing", "decreasing", "stable", "insufficient_data")


class TestRiskScorer:
    def test_low_risk_supplier(self):
        result = score_supplier_risk(
            supplier_id="test-1",
            supplier_name="Good Supplier",
            on_time_rate=0.98,
            defect_rate=0.005,
            avg_delivery_days=5,
            expected_delivery_days=7,
            total_spend=50000,
            portfolio_total_spend=1000000,
            order_count=100,
            country="US",
            years_in_business=15,
        )
        assert result.risk_level == "low"
        assert result.overall_risk_score < 35

    def test_high_risk_supplier(self):
        result = score_supplier_risk(
            supplier_id="test-2",
            supplier_name="Risky Supplier",
            on_time_rate=0.60,
            defect_rate=0.12,
            avg_delivery_days=25,
            expected_delivery_days=10,
            total_spend=400000,
            portfolio_total_spend=1000000,
            order_count=3,
            country="CN",
            years_in_business=1,
        )
        assert result.risk_level in ("high", "critical")
        assert result.overall_risk_score > 55
        assert len(result.factors) == 6

    def test_risk_factors_present(self):
        result = score_supplier_risk(
            supplier_id="test-3", supplier_name="Test",
            on_time_rate=0.9, defect_rate=0.02,
            avg_delivery_days=10, expected_delivery_days=10,
            total_spend=100000, portfolio_total_spend=1000000,
            order_count=50, country="US",
        )
        factor_names = {f.name for f in result.factors}
        assert "Delivery Performance" in factor_names
        assert "Quality Metrics" in factor_names
        assert "Concentration Risk" in factor_names


class TestAnomalyDetector:
    def test_detect_price_spike(self):
        records = []
        for i in range(20):
            records.append({
                "id": i, "item_name": "Widget A", "amount": 100 + np.random.uniform(-10, 10),
                "unit_price": 10, "quantity": 10, "category": "Parts",
                "spend_date": date.today() - timedelta(days=30 * (20 - i)),
            })
        records.append({
            "id": 20, "item_name": "Widget A", "amount": 1000,
            "unit_price": 100, "quantity": 10, "category": "Parts",
            "spend_date": date.today(),
        })

        anomalies = detect_spending_anomalies(records)
        assert len(anomalies) > 0
        assert any(a.id == 20 for a in anomalies)

    def test_no_anomalies_in_uniform_data(self):
        records = [
            {
                "id": i, "item_name": "Widget", "amount": 100,
                "unit_price": 10, "quantity": 10, "category": "Parts",
                "spend_date": date.today() - timedelta(days=i),
            }
            for i in range(30)
        ]
        anomalies = detect_spending_anomalies(records)
        assert len(anomalies) == 0

    def test_too_few_records(self):
        records = [
            {"id": 1, "item_name": "A", "amount": 100, "unit_price": 10,
             "quantity": 10, "category": "X", "spend_date": date.today()},
        ]
        anomalies = detect_spending_anomalies(records)
        assert len(anomalies) == 0
