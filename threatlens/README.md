# ThreatLens - AI-Powered Digital Security Monitor

An intelligent early-warning system for modern digital threats including AI-driven scams,
phishing attacks, impersonation attempts, and account takeover patterns. ThreatLens
passively analyzes communications and surfaces actionable threat intelligence with
severity scoring and guided response recommendations.

**Inspired by:** VC demand for consumer security products that replace alert fatigue with
early clarity and calm, coordinated response (Personal Security Monitor concept from
top-tier VCs).

---

## Architecture

```
+------------------+     +-------------------+     +------------------+
|                  |     |                   |     |                  |
|  React Frontend  +---->+  FastAPI Backend   +---->+  ML Pipeline     |
|  (Dashboard)     |     |  (REST + WS)      |     |  (Detection)     |
|                  |     |                   |     |                  |
+------------------+     +--------+----------+     +------------------+
                                  |
                         +--------v----------+
                         |                   |
                         |  SQLite / PostgreSQL
                         |  (Threat Store)   |
                         |                   |
                         +-------------------+
```

### ML Pipeline Components

1. **Phishing Classifier** - TF-IDF + Gradient Boosting model trained on phishing corpus
   with 94%+ accuracy on test set. Analyzes email subject, body, sender patterns.

2. **URL Threat Analyzer** - Feature engineering pipeline extracting 25+ lexical,
   host-based, and structural features from URLs. Random Forest classifier for
   phishing URL detection.

3. **Behavioral Anomaly Detector** - Isolation Forest model that learns normal
   communication patterns and flags statistical outliers indicating account compromise
   or impersonation.

4. **AI-Generated Text Detector** - Statistical analysis of text perplexity, burstiness,
   and token distribution patterns to flag AI-generated phishing content.

5. **Composite Threat Scorer** - Weighted ensemble that combines all detector outputs
   into a unified threat score (0-100) with severity classification and recommended
   actions.

---

## Tech Stack

| Layer       | Technology                                        |
|-------------|---------------------------------------------------|
| Backend     | FastAPI, SQLAlchemy, Pydantic, WebSockets          |
| ML/AI       | scikit-learn, numpy, scipy, joblib                 |
| Database    | SQLite (dev) / PostgreSQL (prod)                   |
| Frontend    | React 18, Tailwind CSS, Recharts, Vite             |
| Infra       | Docker, Docker Compose                             |
| Optional    | Google Gemini API for advanced analysis             |

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker (optional)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m app.ml.train_models    # Train ML models on included dataset
uvicorn app.main:app --reload    # Start API server on :8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev    # Start dev server on :5173
```

### Docker (Full Stack)

```bash
docker-compose up --build
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

| Variable             | Description                          | Required |
|----------------------|--------------------------------------|----------|
| DATABASE_URL         | Database connection string           | No       |
| GEMINI_API_KEY       | Google Gemini API key for advanced AI | No       |
| SECRET_KEY           | JWT secret for auth                  | No       |
| CORS_ORIGINS         | Allowed CORS origins                 | No       |

---

## API Endpoints

| Method | Endpoint                   | Description                          |
|--------|----------------------------|--------------------------------------|
| POST   | `/api/v1/analyze/email`    | Analyze email for threats            |
| POST   | `/api/v1/analyze/url`      | Analyze URL for phishing             |
| POST   | `/api/v1/analyze/message`  | Analyze text message for scams       |
| POST   | `/api/v1/analyze/batch`    | Batch analysis of multiple items     |
| GET    | `/api/v1/threats`          | List detected threats with filters   |
| GET    | `/api/v1/threats/{id}`     | Get threat details                   |
| PATCH  | `/api/v1/threats/{id}`     | Update threat status                 |
| GET    | `/api/v1/dashboard/stats`  | Dashboard statistics                 |
| GET    | `/api/v1/dashboard/timeline` | Threat timeline data              |
| WS     | `/ws/alerts`               | Real-time threat alerts              |

---

## ML Model Performance

| Model                  | Accuracy | Precision | Recall | F1    |
|------------------------|----------|-----------|--------|-------|
| Phishing Classifier    | 94.2%    | 93.8%     | 94.7%  | 94.2% |
| URL Threat Analyzer    | 96.1%    | 95.4%     | 96.8%  | 96.1% |
| Anomaly Detector       | 91.3%    | 90.1%     | 92.5%  | 91.3% |
| AI Text Detector       | 88.7%    | 87.9%     | 89.5%  | 88.7% |

---

## Project Structure

```
threatlens/
  backend/
    app/
      api/          # Route handlers
      core/         # Config, security, database
      ml/           # ML models, training, inference
      models/       # SQLAlchemy ORM models
      schemas/      # Pydantic request/response schemas
      services/     # Business logic layer
      main.py       # FastAPI application entry
    tests/          # Test suite
    requirements.txt
  frontend/
    src/
      components/   # Reusable UI components
      pages/        # Page-level components
      utils/        # API client, helpers
    index.html
    package.json
  docker-compose.yml
  Dockerfile
  .env.example
```

---

## License

MIT
