# Family OS

Family OS is a portfolio-grade full-stack product inspired by VC requests for software that reduces the cognitive load of keeping families in sync. Instead of focusing on chores and calendars alone, it captures lightweight context, surfaces meaningful memories, and suggests low-effort opportunities for connection.

## Why this stands out

- Demonstrates full-stack ownership with FastAPI, SQLite, and a polished browser dashboard.
- Shows product judgment beyond chatbots: timeline ingestion, derived memories, relationship graphing, and suggestion generation.
- Runs fully offline using deterministic intelligence, while exposing optional Gemini integration hooks to upgrade summaries.
- Maps directly to backend and AI engineering roles by emphasizing data modeling, recommendation logic, and explainable system behavior.

## Features

- Household timeline with mood-aware updates
- Automatic memory capture for milestone moments
- Opportunity engine that spots check-ins, celebrations, and shared interests
- Lightweight relationship graph built from co-occurrence signals
- Weekly family digest with optional Gemini-generated copy

## Run locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --app-dir . --reload
```

Open http://127.0.0.1:8000

## Optional Gemini integration

Set `GEMINI_API_KEY` to let the digest use Gemini when available. The app works without it and falls back to a deterministic summary generator.

## API highlights

- `GET /api/dashboard` returns the full dashboard payload
- `POST /api/updates` adds a family update and can auto-promote milestones into memories
- `POST /api/memories` stores a curated memory manually

## Test

```bash
pytest
```
