# SecureSignal — Real-Time Personal AI Threat Detection

A full-stack security monitoring platform that detects AI-generated scams, phishing attempts, account takeover indicators, and social engineering attacks in real time. No expensive API calls needed for the core detection engine — it runs entirely locally using statistical ML.

Inspired by the Supercharge VC request for "devtools/infra for facial liveness verification" and the broader "Personal Security Monitor" concept addressing AI-driven fraud.

---

## Architecture

```
                    WebSocket
User Browser  <----------------->  FastAPI WS Endpoint
     |                                    |
     |  REST (analysis)                   |  Background Task
     v                                    v
FastAPI REST API              APScheduler Monitor Loop
     |                              (simulates real data
     v                               feeds: email, SMS,
Detection Engine                     account webhooks)
  |                                       |
  |-- PhishingDetector                    |
  |   (regex patterns, URL analysis)      v
  |                               ThreatEvent -> DB
  |-- AITextAnalyzer                      |
  |   (perplexity, burstiness,            v
  |    vocabulary entropy)         Broadcast to all
  |                                 connected WS clients
  |-- RiskScorer
      (weighted composite)

SQLAlchemy + SQLite for persistence
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + async SQLAlchemy |
| Real-time | WebSockets (native FastAPI) |
| Background Jobs | asyncio tasks (monitoring loop) |
| ML Detection | Custom statistical analysis (no API) |
| Frontend | Next.js 14 + TypeScript + Tailwind |
| Visualization | SVG-based risk gauge, D3-inspired |
| Deployment | Docker Compose |

---

## Detection Engine

### AI Text Detection (No API Required)

The `text_analyzer.py` module implements a statistical approach inspired by academic AI detection research:

**Perplexity Proxy**: Measures vocabulary entropy. LLM-generated text uses words more predictably, resulting in lower entropy. Formula: `H = -sum(p * log2(p))` over the token frequency distribution.

**Burstiness Analysis**: Human writing has high variance in sentence length (coefficient of variation > 30%). AI text tends toward uniform sentence length (CV < 25%).

**Bigram Repetition**: AI models frequently repeat n-gram patterns, especially in longer texts. Repetition rates above 15% are flagged.

**Vocabulary Richness**: Type-token ratio. LLMs with diverse training have high lexical diversity; templated scam text does not.

### Phishing Detection

Multi-layer rule-based detection covering:
- Urgency and time pressure language (20+ regex patterns)
- Credential harvesting triggers (15+ patterns)
- Brand impersonation (30+ major brands)
- Financial scam indicators (advance fee, prize fraud, etc.)
- URL structural analysis (TLD risk scoring, subdomain depth, lookalike detection)

### Composite Risk Scoring

```python
composite = (phishing_score * 0.7) + (ai_probability * 0.3)

# AI-assisted phishing gets elevated score
if ai_probability > 0.6 and phishing_score > 0.3:
    composite = min(composite * 1.25, 1.0)
```

---

## Project Structure

```
secure-signal/
  backend/
    app/
      detection/
        text_analyzer.py      # Statistical AI text detection
        phishing_detector.py  # Pattern-based phishing detection
        risk_scorer.py        # Composite risk scoring
      routers/
        analysis.py           # REST analysis endpoints
        websocket.py          # WebSocket threat broadcaster
      background/
        monitor.py            # Threat simulation / monitoring loop
      models.py
      database.py
      main.py
  frontend/
    app/page.tsx              # Real-time dashboard
    components/
      ThreatCard.tsx          # Expandable threat display
      AnalysisPanel.tsx       # Content analysis UI
      RiskGauge.tsx           # SVG semicircle gauge
    lib/api.ts
    types/index.ts
  docker-compose.yml
```

---

## Getting Started

### Backend

```bash
cd secure-signal/backend
cp .env.example .env

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### Frontend

```bash
cd secure-signal/frontend
cp .env.local.example .env.local
npm install
npm run dev -- --port 3001
```

Open [http://localhost:3001](http://localhost:3001)

### Docker

```bash
cd secure-signal
docker compose up --build
```

---

## Demo Scenarios

**Paste these into the analysis panel:**

High-risk phishing:
```
Dear Customer, Your PayPal account has been suspended due to unusual activity.
You must verify your account immediately within 24 hours or your account will
be permanently closed. Click here to verify: http://paypal-verify-secure.tk/login
```

AI-generated scam:
```
Congratulations! You have been selected as the winner of our annual customer
loyalty program. Your prize of $5,000 has been approved for immediate transfer.
To claim your reward, you must verify your identity by providing your banking
information within 48 hours.
```

The monitor tab shows a live feed of simulated threats arriving via WebSocket every 8-15 seconds.

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/analyze` | POST | Analyze content for threats |
| `/api/analyze/threats` | GET | Get active threat events |
| `/api/analyze/threats/{id}/dismiss` | POST | Dismiss a threat |
| `/api/analyze/history` | GET | Analysis history |
| `/api/stats` | GET | Dashboard statistics |
| `/ws/threats` | WS | Real-time threat stream |

---

## Scaling to Production

To make this production-ready with real data sources:

1. **Email monitoring**: Integrate Gmail/Outlook webhooks to scan incoming mail
2. **Account monitoring**: OAuth connections to Google, Apple, GitHub to watch for anomalous logins
3. **Call monitoring**: Twilio webhook integration to analyze inbound call patterns
4. **Browser extension**: Content script to analyze emails in webmail clients
5. **ML upgrade**: Replace heuristic AI detector with a fine-tuned classifier (e.g., BERT-based)
