# ProcureFlow AI

ProcureFlow AI is an AI-assisted direct procurement command center inspired by investor requests for products that can turn messy operational data into better sourcing decisions. It focuses on unstructured supplier inputs, quote scoring, demand forecasting, and audit-friendly recommendations.

## Why this stands out

- Feels like a real internal product instead of a CRUD demo: sourcing decisions, supplier trade-offs, pricing outliers, and forecast intelligence.
- Demonstrates backend and systems thinking with weighted optimization, explainable recommendations, and category-level forecasts.
- Works without paid APIs while leaving room to plug in LLM enrichment for supplier notes or negotiation summaries later.

## Features

- Supplier master with reliability, quality, risk, and certification metadata
- Requisition and quote workflows with recommendation explanations
- Demand forecast by category using local trend fitting
- Price anomaly detection to spot unusual supplier bids

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
