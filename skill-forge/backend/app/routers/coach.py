import uuid
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from ..database import get_db
from ..models import Learner, CoachSession, CoachMessage, AssessmentResult
from ..agents import stream_coaching_response, assess_skill_answer, get_assessment_questions

router = APIRouter(prefix="/coach", tags=["coach"])


class ChatRequest(BaseModel):
    learner_id: str
    message: str
    skill_id: Optional[str] = "llm_basics"
    session_id: Optional[str] = None


class AssessRequest(BaseModel):
    learner_id: str
    skill_id: str
    question: str
    answer: str


@router.post("/chat/stream")
async def chat_stream(body: ChatRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Learner).where(Learner.id == body.learner_id))
    learner = result.scalar_one_or_none()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    session_id = body.session_id
    if not session_id:
        session = CoachSession(
            id=str(uuid.uuid4()),
            learner_id=body.learner_id,
            title=f"Session: {body.skill_id}"
        )
        db.add(session)
        await db.commit()
        session_id = session.id
    else:
        sess_result = await db.execute(select(CoachSession).where(CoachSession.id == session_id))
        if not sess_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Session not found")

    history_result = await db.execute(
        select(CoachMessage)
        .where(CoachMessage.session_id == session_id)
        .order_by(CoachMessage.created_at)
        .limit(20)
    )
    history = [{"role": m.role, "content": m.content} for m in history_result.scalars().all()]

    human_msg = CoachMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="user",
        content=body.message,
        skill_context=body.skill_id
    )
    db.add(human_msg)
    await db.commit()

    learner_dict = {
        "name": learner.name,
        "role": learner.role,
        "experience_level": learner.experience_level,
        "mastered_skills": learner.mastered_skills or [],
        "xp_points": learner.xp_points
    }

    full_response = []

    async def generate():
        nonlocal full_response
        async for token in stream_coaching_response(
            messages=history + [{"role": "user", "content": body.message}],
            skill_id=body.skill_id or "llm_basics",
            learner=learner_dict
        ):
            full_response.append(token)
            yield f"data: {json.dumps({'type': 'token', 'content': token, 'session_id': session_id})}\n\n"

        content = "".join(full_response)
        ai_msg = CoachMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="assistant",
            content=content,
            skill_context=body.skill_id
        )
        async with db.begin():
            db.add(ai_msg)

        yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@router.get("/sessions/{learner_id}")
async def get_sessions(learner_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CoachSession)
        .where(CoachSession.learner_id == learner_id)
        .order_by(CoachSession.created_at.desc())
    )
    sessions = result.scalars().all()
    return [{"id": s.id, "title": s.title, "created_at": s.created_at.isoformat()} for s in sessions]


@router.get("/sessions/{learner_id}/{session_id}/messages")
async def get_messages(learner_id: str, session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CoachMessage)
        .where(CoachMessage.session_id == session_id)
        .order_by(CoachMessage.created_at)
    )
    msgs = result.scalars().all()
    return [{"id": m.id, "role": m.role, "content": m.content, "skill_context": m.skill_context, "created_at": m.created_at.isoformat()} for m in msgs]


@router.post("/assess")
async def run_assessment(body: AssessRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Learner).where(Learner.id == body.learner_id))
    learner = result.scalar_one_or_none()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    assessment = await assess_skill_answer(
        skill_id=body.skill_id,
        question=body.question,
        answer=body.answer
    )

    ar = AssessmentResult(
        id=str(uuid.uuid4()),
        learner_id=body.learner_id,
        skill_id=body.skill_id,
        score=assessment.get("score", 0.5),
        level=assessment.get("level", "intermediate"),
        details=assessment
    )
    db.add(ar)

    if assessment.get("score", 0) >= 0.8:
        current_mastered = list(learner.mastered_skills or [])
        if body.skill_id not in current_mastered:
            current_mastered.append(body.skill_id)
            learner.mastered_skills = current_mastered
            learner.xp_points = (learner.xp_points or 0) + 100

    await db.commit()
    return {**assessment, "xp_gained": 100 if assessment.get("score", 0) >= 0.8 else 0}


@router.get("/questions/{skill_id}")
async def get_questions(skill_id: str):
    questions = get_assessment_questions(skill_id)
    return {"skill_id": skill_id, "questions": questions}
