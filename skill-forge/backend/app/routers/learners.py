import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from ..database import get_db
from ..models import Learner
from ..graph import get_skill_graph

router = APIRouter(prefix="/learners", tags=["learners"])


class CreateLearnerRequest(BaseModel):
    name: str
    role: Optional[str] = "Software Engineer"
    experience_level: Optional[str] = "intermediate"
    initial_skills: Optional[list[str]] = []


class UpdateSkillsRequest(BaseModel):
    mastered_skills: list[str]
    target_skills: Optional[list[str]] = []


class LearnerResponse(BaseModel):
    id: str
    name: str
    role: str
    experience_level: str
    mastered_skills: list
    learning_path: list
    xp_points: int
    streak_days: int
    created_at: str


@router.post("", response_model=LearnerResponse)
async def create_learner(body: CreateLearnerRequest, db: AsyncSession = Depends(get_db)):
    skill_graph = get_skill_graph()
    validated_skills = [s for s in (body.initial_skills or []) if skill_graph.get_skill(s)]

    learning_path = skill_graph.compute_learning_path(
        mastered=validated_skills,
        target_skills=["ai_agents", "rag_systems", "langgraph"]
    )

    learner = Learner(
        id=str(uuid.uuid4()),
        name=body.name,
        role=body.role or "Software Engineer",
        experience_level=body.experience_level or "intermediate",
        mastered_skills=validated_skills,
        learning_path=[p["id"] for p in learning_path],
        xp_points=len(validated_skills) * 50
    )
    db.add(learner)
    await db.commit()
    await db.refresh(learner)

    return LearnerResponse(
        id=learner.id,
        name=learner.name,
        role=learner.role,
        experience_level=learner.experience_level,
        mastered_skills=learner.mastered_skills,
        learning_path=learning_path,
        xp_points=learner.xp_points,
        streak_days=learner.streak_days,
        created_at=learner.created_at.isoformat()
    )


@router.get("/{learner_id}", response_model=LearnerResponse)
async def get_learner(learner_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Learner).where(Learner.id == learner_id))
    learner = result.scalar_one_or_none()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    skill_graph = get_skill_graph()
    learning_path = skill_graph.compute_learning_path(
        mastered=learner.mastered_skills or [],
        target_skills=["ai_agents", "rag_systems", "langgraph", "fine_tuning"]
    )

    return LearnerResponse(
        id=learner.id,
        name=learner.name,
        role=learner.role,
        experience_level=learner.experience_level,
        mastered_skills=learner.mastered_skills or [],
        learning_path=learning_path,
        xp_points=learner.xp_points,
        streak_days=learner.streak_days,
        created_at=learner.created_at.isoformat()
    )


@router.put("/{learner_id}/skills")
async def update_skills(learner_id: str, body: UpdateSkillsRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Learner).where(Learner.id == learner_id))
    learner = result.scalar_one_or_none()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    skill_graph = get_skill_graph()
    new_mastered = [s for s in body.mastered_skills if skill_graph.get_skill(s)]
    xp_gain = max(0, len(new_mastered) - len(learner.mastered_skills or [])) * 100
    learner.mastered_skills = new_mastered
    learner.xp_points = (learner.xp_points or 0) + xp_gain

    learning_path = skill_graph.compute_learning_path(
        mastered=new_mastered,
        target_skills=body.target_skills or ["ai_agents", "rag_systems"]
    )
    learner.learning_path = [p["id"] for p in learning_path]

    await db.commit()
    return {"status": "updated", "xp_gained": xp_gain, "new_xp_total": learner.xp_points, "learning_path": learning_path}
