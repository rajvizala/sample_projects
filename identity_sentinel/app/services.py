from __future__ import annotations

import json
from collections import Counter
from statistics import mean

import numpy as np
from sklearn.ensemble import IsolationForest

from . import models

RISKY_TERMS = {
    'urgent', 'wire', 'gift card', 'crypto', 'verify account', 'otp', 'password',
    'suspended', 'bank', 'social security', 'act now', 'refund', 'invoice'
}
TRUSTED_SENDERS = {'Mom', 'Dad', 'BankApp', 'Payroll', 'Nia School', 'Kabir Coach'}
SAFE_COUNTRY = 'US'


def serialize_signal(signal: models.SignalEvent) -> dict:
    return {
        'id': signal.id,
        'channel': signal.channel,
        'sender': signal.sender,
        'content': signal.content,
        'country': signal.country,
        'hour': signal.hour,
        'amount': signal.amount,
        'new_device': signal.new_device,
        'new_ip': signal.new_ip,
        'ai_voice_flag': signal.ai_voice_flag,
        'created_at': signal.created_at.isoformat(),
    }


def serialize_alert(alert: models.Alert) -> dict:
    return {
        'id': alert.id,
        'signal_id': alert.signal_id,
        'severity': alert.severity,
        'score': round(alert.score, 1),
        'summary': alert.summary,
        'reasons': json.loads(alert.reasons),
        'action': alert.action,
        'created_at': alert.created_at.isoformat(),
    }


def _count_risky_terms(text: str) -> int:
    lowered = text.lower()
    return sum(1 for term in RISKY_TERMS if term in lowered)


def _vectorize(signal: models.SignalEvent) -> list[float]:
    risky_terms = _count_risky_terms(signal.content)
    odd_hour = 1.0 if signal.hour < 6 or signal.hour > 22 else 0.0
    foreign = 1.0 if signal.country != SAFE_COUNTRY else 0.0
    unknown_sender = 1.0 if signal.sender not in TRUSTED_SENDERS else 0.0
    channel_risk = {'sms': 0.7, 'email': 0.6, 'login': 0.8, 'payment': 0.9, 'voice': 1.0}.get(signal.channel, 0.5)
    return [
        risky_terms,
        odd_hour,
        foreign,
        unknown_sender,
        float(signal.new_device),
        float(signal.new_ip),
        float(signal.ai_voice_flag),
        min(signal.amount / 1000.0, 5.0),
        channel_risk,
    ]


def _fit_model(history: list[models.SignalEvent]) -> IsolationForest | None:
    if len(history) < 6:
        return None
    matrix = np.array([_vectorize(item) for item in history])
    return IsolationForest(random_state=42, contamination=0.18).fit(matrix)


def assess_signal(signal: models.SignalEvent, history: list[models.SignalEvent]) -> dict:
    reasons = []
    risky_terms = _count_risky_terms(signal.content)
    if risky_terms:
        reasons.append(f'{risky_terms} known scam phrases detected')
    if signal.sender not in TRUSTED_SENDERS:
        reasons.append('sender is not on the normal trust list')
    if signal.country != SAFE_COUNTRY:
        reasons.append(f'unexpected origin country: {signal.country}')
    if signal.hour < 6 or signal.hour > 22:
        reasons.append('arrived outside normal communication hours')
    if signal.new_device:
        reasons.append('activity came from a new device')
    if signal.new_ip:
        reasons.append('activity came from a new network location')
    if signal.ai_voice_flag:
        reasons.append('signal includes an AI voice manipulation flag')
    if signal.amount >= 400:
        reasons.append(f'requested amount is unusually high at ${signal.amount:,.0f}')

    rule_score = (
        risky_terms * 10
        + (12 if signal.sender not in TRUSTED_SENDERS else 0)
        + (12 if signal.country != SAFE_COUNTRY else 0)
        + (8 if signal.hour < 6 or signal.hour > 22 else 0)
        + (12 if signal.new_device else 0)
        + (12 if signal.new_ip else 0)
        + (16 if signal.ai_voice_flag else 0)
        + min(signal.amount / 35.0, 18)
    )

    model = _fit_model(history)
    anomaly_component = 0.0
    if model is not None:
        score = model.decision_function(np.array([_vectorize(signal)]))[0]
        anomaly_component = max(0.0, min(28.0, (0.35 - score) * 55))
        if anomaly_component >= 8:
            reasons.append('behavior deviates from baseline event history')

    final_score = min(99.0, rule_score + anomaly_component)
    if final_score >= 78:
        severity = 'critical'
    elif final_score >= 58:
        severity = 'high'
    elif final_score >= 34:
        severity = 'medium'
    else:
        severity = 'low'

    if severity == 'critical':
        action = 'Freeze sensitive actions, verify through a second trusted channel, and rotate passwords or session tokens now.'
    elif severity == 'high':
        action = 'Do not respond in-channel. Verify sender identity independently and place temporary holds on financial or account changes.'
    elif severity == 'medium':
        action = 'Slow down, verify context, and avoid sharing codes or approving changes until identity is confirmed.'
    else:
        action = 'Log the event and keep monitoring. No urgent intervention is needed yet.'

    summary = f'{severity.title()} risk {signal.channel} event from {signal.sender} scored {final_score:.0f}/100.'
    return {
        'severity': severity,
        'score': final_score,
        'summary': summary,
        'reasons': reasons or ['no significant anomalies detected'],
        'action': action,
    }


def dashboard_metrics(signals: list[models.SignalEvent], alerts: list[models.Alert]) -> dict:
    if not signals:
        return {'total_signals': 0, 'average_score': 0, 'critical_alerts': 0, 'channels': {}}
    channel_mix = Counter(item.channel for item in signals)
    avg_score = mean(alert.score for alert in alerts) if alerts else 0
    critical = sum(1 for alert in alerts if alert.severity == 'critical')
    return {
        'total_signals': len(signals),
        'average_score': round(avg_score, 1),
        'critical_alerts': critical,
        'channels': dict(channel_mix),
    }
