# Identity Sentinel

Identity Sentinel is an AI-native personal security monitor inspired by VC demand for early-warning systems against impersonation, scams, and account takeover. It ingests cross-channel identity signals, compares them against normal behavior, and produces explainable risk assessments with action playbooks.

## Why this stands out

- Goes beyond generic fraud dashboards by combining rules, anomaly detection, and response guidance.
- Demonstrates backend engineering through event ingestion, scoring pipelines, persistence, and audit-ready alert generation.
- Shows ML judgment with a local Isolation Forest baseline that works offline and without expensive APIs.
- Includes optional Gemini integration hooks for richer executive summaries later.

## Features

- Unified signal ingestion for SMS, email, login, payment, and voice scenarios
- Hybrid risk scoring: lexical scam cues, behavioral mismatches, and anomaly model output
- Explainable alert reasons with severity levels and recommended actions
- Risk dashboard for recent signals, channel distribution, and critical cases

## Run locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --app-dir . --reload
```

Open http://127.0.0.1:8000

## Test

```bash
pytest
```
