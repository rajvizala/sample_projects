import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from ..database import get_db
from ..models import Session, Message

router = APIRouter(prefix="/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    name: Optional[str] = "New Session"
    business_context: Optional[dict] = {}


class SessionResponse(BaseModel):
    id: str
    name: str
    business_context: dict
    created_at: str

    class Config:
        from_attributes = True


@router.post("", response_model=SessionResponse)
async def create_session(body: CreateSessionRequest, db: AsyncSession = Depends(get_db)):
    session = Session(
        id=str(uuid.uuid4()),
        name=body.name or "New Session",
        business_context=body.business_context or {}
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return SessionResponse(
        id=session.id,
        name=session.name,
        business_context=session.business_context,
        created_at=session.created_at.isoformat()
    )


@router.get("", response_model=list[SessionResponse])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).order_by(Session.created_at.desc()))
    sessions = result.scalars().all()
    return [
        SessionResponse(
            id=s.id,
            name=s.name,
            business_context=s.business_context,
            created_at=s.created_at.isoformat()
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(
        id=session.id,
        name=session.name,
        business_context=session.business_context,
        created_at=session.created_at.isoformat()
    )


@router.put("/{session_id}/context")
async def update_context(session_id: str, context: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.business_context = context
    await db.commit()
    return {"status": "updated"}


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    agent: Optional[str]
    created_at: str


@router.get("/{session_id}/messages", response_model=list[MessageResponse])
async def get_messages(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Message).where(Message.session_id == session_id).order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return [
        MessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            agent=m.agent,
            created_at=m.created_at.isoformat()
        )
        for m in messages
    ]
