"""
Demand forecasting engine for procurement planning.
Uses exponential smoothing and ARIMA for time series prediction
with automatic seasonality detection.
"""

import numpy as np
from datetime import date, timedelta

from app.schemas.procurement import ForecastPoint, ForecastResponse


def exponential_smoothing(series: np.ndarray, alpha: float = 0.3) -> np.ndarray:
    """Simple exponential smoothing."""
    result = np.zeros(len(series))
    result[0] = series[0]
    for i in range(1, len(series)):
        result[i] = alpha * series[i] + (1 - alpha) * result[i - 1]
    return result


def double_exponential_smoothing(
    series: np.ndarray, alpha: float = 0.3, beta: float = 0.1, periods: int = 12
) -> np.ndarray:
    """Holt's double exponential smoothing with trend."""
    if len(series) < 2:
        return np.full(periods, series[0] if len(series) > 0 else 0)

    level = series[0]
    trend = series[1] - series[0]
    forecast = []

    for val in series:
        prev_level = level
        level = alpha * val + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend

    for i in range(1, periods + 1):
        forecast.append(level + i * trend)

    return np.array(forecast)


def detect_seasonality(series: np.ndarray, max_period: int = 12) -> int | None:
    """Detect seasonality period using autocorrelation."""
    if len(series) < max_period * 2:
        return None

    mean = np.mean(series)
    std = np.std(series)
    if std == 0:
        return None

    normalized = (series - mean) / std
    best_period = None
    best_corr = 0.3

    for period in range(2, min(max_period + 1, len(series) // 2)):
        corr = np.corrcoef(normalized[:-period], normalized[period:])[0, 1]
        if corr > best_corr:
            best_corr = corr
            best_period = period

    return best_period


def forecast_demand(
    dates: list[date],
    quantities: list[float],
    amounts: list[float],
    periods: int = 12,
    category: str = "general",
) -> ForecastResponse:
    """Generate demand forecast from historical procurement data."""
    qty_series = np.array(quantities, dtype=float)
    amt_series = np.array(amounts, dtype=float)

    seasonality = detect_seasonality(qty_series)
    has_seasonality = seasonality is not None

    if len(qty_series) >= 4:
        qty_forecast = double_exponential_smoothing(qty_series, alpha=0.4, beta=0.15, periods=periods)
        amt_forecast = double_exponential_smoothing(amt_series, alpha=0.4, beta=0.15, periods=periods)
    else:
        avg_qty = np.mean(qty_series) if len(qty_series) > 0 else 0
        avg_amt = np.mean(amt_series) if len(amt_series) > 0 else 0
        qty_forecast = np.full(periods, avg_qty)
        amt_forecast = np.full(periods, avg_amt)

    qty_forecast = np.maximum(qty_forecast, 0)
    amt_forecast = np.maximum(amt_forecast, 0)

    if len(qty_series) > 1:
        residual_std = np.std(qty_series - exponential_smoothing(qty_series))
    else:
        residual_std = np.std(qty_series) if len(qty_series) > 0 else 0

    last_date = dates[-1] if dates else date.today()
    forecast_points = []

    for i in range(periods):
        forecast_date = last_date + timedelta(days=30 * (i + 1))
        width = 1.96 * residual_std * np.sqrt(i + 1)
        forecast_points.append(ForecastPoint(
            date=forecast_date.isoformat(),
            predicted_quantity=round(float(qty_forecast[i]), 1),
            predicted_spend=round(float(amt_forecast[i]), 2),
            confidence_lower=round(max(float(amt_forecast[i]) - width * (np.mean(amt_series) / max(np.mean(qty_series), 1)), 0), 2),
            confidence_upper=round(float(amt_forecast[i]) + width * (np.mean(amt_series) / max(np.mean(qty_series), 1)), 2),
        ))

    if len(qty_series) >= 2:
        recent_trend = np.polyfit(range(len(qty_series)), qty_series, 1)[0]
        if recent_trend > 0.5:
            trend = "increasing"
        elif recent_trend < -0.5:
            trend = "decreasing"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"

    return ForecastResponse(
        category=category,
        model_type="double_exponential_smoothing",
        historical_points=len(quantities),
        forecast=forecast_points,
        trend=trend,
        seasonality_detected=has_seasonality,
        next_period_estimate=round(float(amt_forecast[0]), 2) if len(amt_forecast) > 0 else 0,
    )
