from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from . import models
from .db import Base, SessionLocal, engine, get_db
from .schemas import QuoteCreate, RequisitionCreate
from .seed import seed_data
from .services import (
    forecast_demand,
    price_anomalies,
    recommend_quote,
    serialize_quote,
    serialize_requisition,
    serialize_supplier,
)

app = FastAPI(title='ProcureFlow AI', version='1.0.0')
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
    suppliers = db.execute(select(models.Supplier).order_by(models.Supplier.name)).scalars().all()
    requisitions = db.execute(select(models.Requisition).order_by(models.Requisition.created_at.desc())).scalars().all()
    quotes = db.execute(
        select(models.Quote)
        .options(joinedload(models.Quote.supplier), joinedload(models.Quote.requisition))
    ).scalars().all()
    demand_signals = db.execute(select(models.DemandSignal)).scalars().all()
    by_requisition = {}
    for requisition in requisitions:
        candidate_quotes = [quote for quote in quotes if quote.requisition_id == requisition.id]
        by_requisition[requisition.id] = recommend_quote(requisition, candidate_quotes)
    return {
        'suppliers': [serialize_supplier(item) for item in suppliers],
        'requisitions': [serialize_requisition(item) for item in requisitions],
        'quotes': [serialize_quote(item) for item in quotes],
        'recommendations': by_requisition,
        'forecasts': forecast_demand(demand_signals),
        'price_anomalies': price_anomalies(quotes),
    }


@app.get('/api/dashboard')
def get_dashboard(db: Session = Depends(get_db)) -> dict:
    return dashboard_payload(db)


@app.post('/api/requisitions')
def create_requisition(payload: RequisitionCreate, db: Session = Depends(get_db)) -> dict:
    requisition = models.Requisition(
        title=payload.title,
        category=payload.category,
        quantity=payload.quantity,
        needed_by=payload.needed_by,
        priority=payload.priority,
        required_certifications=', '.join(payload.required_certifications),
    )
    db.add(requisition)
    db.commit()
    db.refresh(requisition)
    return {'requisition': serialize_requisition(requisition), 'dashboard': dashboard_payload(db)}


@app.post('/api/quotes')
def create_quote(payload: QuoteCreate, db: Session = Depends(get_db)) -> dict:
    quote = models.Quote(**payload.model_dump())
    db.add(quote)
    db.commit()
    db.refresh(quote)
    quote = db.execute(
        select(models.Quote)
        .options(joinedload(models.Quote.supplier), joinedload(models.Quote.requisition))
        .where(models.Quote.id == quote.id)
    ).scalar_one()
    return {'quote': serialize_quote(quote), 'dashboard': dashboard_payload(db)}
