import json
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models
from .db import Base, SessionLocal, engine, get_db
from .schemas import SignalCreate
from .seed import seed_data
from .services import assess_signal, dashboard_metrics, serialize_alert, serialize_signal

app = FastAPI(title='Identity Sentinel', version='1.0.0')
static_dir = Path(__file__).resolve().parent / 'static'
app.mount('/static', StaticFiles(directory=static_dir), name='static')


@app.on_event('startup')
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_data(db)


@app.get('/')
def index() -> FileResponse:
    return FileResponse(static_dir / 'index.html')


def dashboard_payload(db: Session) -> dict:
    signals = db.execute(select(models.SignalEvent).order_by(models.SignalEvent.created_at.desc())).scalars().all()
    alerts = db.execute(select(models.Alert).order_by(models.Alert.created_at.desc())).scalars().all()
    return {
        'metrics': dashboard_metrics(signals, alerts),
        'signals': [serialize_signal(item) for item in signals[:12]],
        'alerts': [serialize_alert(item) for item in alerts[:10]],
        'playbooks': [
            {'title': 'Impersonation call', 'steps': ['Hang up', 'Call back via saved number', 'Reset high-value accounts if pressure persists']},
            {'title': 'Account takeover attempt', 'steps': ['Revoke active sessions', 'Reset password', 'Enable stronger MFA']},
            {'title': 'Payment or wire request', 'steps': ['Verify off-channel', 'Set temporary transfer blocks', 'Escalate to bank if already sent']},
        ],
    }


@app.get('/api/dashboard')
def get_dashboard(db: Session = Depends(get_db)) -> dict:
    return dashboard_payload(db)


@app.post('/api/signals')
def ingest_signal(payload: SignalCreate, db: Session = Depends(get_db)) -> dict:
    signal = models.SignalEvent(**payload.model_dump())
    db.add(signal)
    db.flush()

    history = db.execute(
        select(models.SignalEvent)
        .where(models.SignalEvent.id != signal.id)
        .order_by(models.SignalEvent.created_at.desc())
    ).scalars().all()
    assessment = assess_signal(signal, history)
    alert = models.Alert(
        signal_id=signal.id,
        severity=assessment['severity'],
        score=assessment['score'],
        summary=assessment['summary'],
        reasons=json.dumps(assessment['reasons']),
        action=assessment['action'],
    )
    db.add(alert)
    db.commit()
    db.refresh(signal)
    db.refresh(alert)
    return {
        'signal': serialize_signal(signal),
        'alert': serialize_alert(alert),
        'dashboard': dashboard_payload(db),
    }
