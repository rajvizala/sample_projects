# ProcureIQ - AI Procurement Intelligence Platform

An AI-powered procurement intelligence system that transforms unstructured procurement
data into actionable insights. ProcureIQ processes invoices and purchase orders, forecasts
demand patterns, scores supplier risk, and detects spending anomalies -- automating the
analysis that traditionally requires teams of procurement analysts.

**Inspired by:** Veronica Orellana (Partner at CRV) seeking companies tackling the direct
procurement market with AI -- processing unstructured data, automating high-volume
decisions, and creating wedges into demand forecasting, pricing optimization, and
supplier management.

---

## Architecture

```
+-----------------+     +------------------+     +--------------------+
|                 |     |                  |     |                    |
| React Frontend  +---->+ FastAPI Backend  +---->+ ML Pipeline        |
| (Dashboard)     |     | (REST API)       |     | (NLP + Forecasting)|
|                 |     |                  |     |                    |
+-----------------+     +--------+---------+     +--------------------+
                                 |
                    +------------+------------+
                    |                         |
              +-----v------+          +-------v------+
              |            |          |              |
              | PostgreSQL |          | Event Queue  |
              | / SQLite   |          | (In-memory)  |
              |            |          |              |
              +------------+          +--------------+
```

### ML Pipeline Components

1. **Document Parser** - NLP-powered extraction engine that pulls structured data
   (vendor, amounts, line items, dates, payment terms) from unstructured invoice
   and PO text using regex patterns, named entity recognition, and LLM-assisted parsing.

2. **Demand Forecaster** - Time series forecasting using exponential smoothing and
   ARIMA models with automatic seasonality detection. Produces point forecasts with
   confidence intervals for procurement planning.

3. **Supplier Risk Scorer** - Multi-factor risk assessment combining delivery
   performance, financial stability proxies, concentration risk, compliance signals,
   and market volatility indicators into a composite risk score.

4. **Spend Anomaly Detector** - Statistical anomaly detection using Isolation Forest
   and Z-score methods to flag unusual spending patterns, price spikes, duplicate
   payments, and budget deviations.

5. **Pricing Optimizer** - Market-aware pricing model that analyzes historical
   purchase prices, supplier quotes, and market indices to recommend optimal
   purchase timing and negotiation targets.

---

## Tech Stack

| Layer       | Technology                                          |
|-------------|-----------------------------------------------------|
| Backend     | FastAPI, SQLAlchemy, Pydantic, Celery-compatible     |
| ML/AI       | scikit-learn, statsmodels, numpy, scipy               |
| NLP         | regex + rule-based NER, optional Gemini integration   |
| Database    | SQLite (dev) / PostgreSQL (prod)                      |
| Frontend    | React 18, Tailwind CSS, Recharts, Vite                |
| Infra       | Docker, Docker Compose                                |

---

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m app.ml.seed_data         # Seed sample procurement data
uvicorn app.main:app --reload      # Start API on :8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker

```bash
docker-compose up --build
```

---

## API Endpoints

| Method | Endpoint                         | Description                          |
|--------|----------------------------------|--------------------------------------|
| POST   | `/api/v1/documents/parse`        | Parse invoice/PO text into structured data |
| POST   | `/api/v1/documents/upload`       | Upload document for processing       |
| GET    | `/api/v1/suppliers`              | List suppliers with risk scores      |
| GET    | `/api/v1/suppliers/{id}`         | Supplier detail with history         |
| GET    | `/api/v1/suppliers/{id}/risk`    | Detailed risk assessment             |
| GET    | `/api/v1/forecast`               | Demand forecast for items            |
| POST   | `/api/v1/forecast/generate`      | Generate new forecast                |
| GET    | `/api/v1/analytics/spend`        | Spend analytics and breakdown        |
| GET    | `/api/v1/analytics/anomalies`    | Detected spending anomalies          |
| GET    | `/api/v1/analytics/savings`      | Savings opportunities                |
| GET    | `/api/v1/dashboard/overview`     | Dashboard summary metrics            |

---

## Project Structure

```
procure_iq/
  backend/
    app/
      api/          # Route handlers
      core/         # Config, database, event bus
      ml/           # ML models, NLP parser, forecaster
      models/       # SQLAlchemy ORM models
      schemas/      # Pydantic schemas
      services/     # Business logic
      main.py       # FastAPI entry
    tests/
    requirements.txt
  frontend/
    src/
      components/   # UI components
      pages/        # Page components
      utils/        # API client
  docker-compose.yml
  Dockerfile
```

---

## License

MIT
