from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from . import models
from .db import Base, SessionLocal, engine, get_db
from .schemas import MemoryCreate, UpdateCreate
from .seed import seed_data
from .services import (
    build_digest,
    build_graph,
    generate_suggestions,
    maybe_capture_memory,
    serialize_memory,
    serialize_person,
    serialize_update,
)

app = FastAPI(title='Family OS', version='1.0.0')
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
    people = db.execute(select(models.Person).order_by(models.Person.name)).scalars().all()
    updates = db.execute(
        select(models.Update)
        .options(selectinload(models.Update.person))
        .order_by(models.Update.created_at.desc())
    ).scalars().all()
    memories = db.execute(select(models.Memory).order_by(models.Memory.importance.desc(), models.Memory.created_at.desc())).scalars().all()
    suggestions = generate_suggestions(people, updates)
    return {
        'people': [serialize_person(person) for person in people],
        'updates': [serialize_update(item) for item in updates[:12]],
        'memories': [serialize_memory(item) for item in memories[:8]],
        'suggestions': suggestions,
        'graph': build_graph(people, updates[:12], memories[:8]),
        'digest': build_digest(people, updates, suggestions),
    }


@app.get('/api/dashboard')
def get_dashboard(db: Session = Depends(get_db)) -> dict:
    return dashboard_payload(db)


@app.post('/api/updates')
def create_update(payload: UpdateCreate, db: Session = Depends(get_db)) -> dict:
    person = db.get(models.Person, payload.person_id)
    if person is None:
        return {'error': 'Person not found'}
    update = models.Update(
        person_id=payload.person_id,
        category=payload.category.strip(),
        text=payload.text.strip(),
        mood=payload.mood.strip(),
    )
    db.add(update)
    db.flush()
    captured = maybe_capture_memory(payload.text, [person.name])
    if captured:
        title, detail = captured
        db.add(models.Memory(title=title, detail=detail, people=person.name, importance=4))
    db.commit()
    db.refresh(update)
    db.refresh(person)
    return {'update': serialize_update(update), 'dashboard': dashboard_payload(db)}


@app.post('/api/memories')
def create_memory(payload: MemoryCreate, db: Session = Depends(get_db)) -> dict:
    memory = models.Memory(
        title=payload.title.strip(),
        detail=payload.detail.strip(),
        people=', '.join(payload.people),
        importance=payload.importance,
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return {'memory': serialize_memory(memory)}
