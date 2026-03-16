from fastapi import APIRouter, Query
from ..graph import get_skill_graph

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("")
async def get_full_graph():
    skill_graph = get_skill_graph()
    return skill_graph.get_full_graph()


@router.get("/skill/{skill_id}")
async def get_skill(skill_id: str):
    skill_graph = get_skill_graph()
    skill = skill_graph.get_skill(skill_id)
    if not skill:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Skill not found")

    return {
        **skill,
        "prerequisites": skill_graph.get_prerequisites(skill_id),
        "next_skills": skill_graph.get_next_skills(skill_id)
    }


@router.get("/path")
async def compute_path(
    mastered: str = Query(default="", description="Comma-separated mastered skill IDs"),
    targets: str = Query(default="ai_agents,rag_systems", description="Comma-separated target skill IDs")
):
    skill_graph = get_skill_graph()
    mastered_list = [s.strip() for s in mastered.split(",") if s.strip()]
    target_list = [s.strip() for s in targets.split(",") if s.strip()]
    path = skill_graph.compute_learning_path(mastered_list, target_list)
    return {"path": path, "total_steps": len(path), "estimated_total_hours": sum(p["estimated_hours"] for p in path)}


@router.get("/search")
async def search_skills(q: str = Query(...)):
    skill_graph = get_skill_graph()
    return skill_graph.search_skills(q)


@router.get("/categories")
async def get_categories():
    skill_graph = get_skill_graph()
    return skill_graph.get_skill_categories()
