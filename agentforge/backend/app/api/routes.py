"""
API routes for AgentForge multi-agent orchestration platform.
"""

import json
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.agents.base import AgentRegistry
from app.agents.tools import ToolRegistry
from app.agents import builtin  # noqa: F401 -- registers agents
from app.engine.workflow import (
    WorkflowEngine, WorkflowDefinition, WorkflowNode, get_engine,
)
from app.models.workflow import WorkflowModel, ExecutionModel
from app.schemas.workflow import (
    AgentExecuteRequest,
    CreateWorkflowRequest,
    WorkflowNodeSchema,
)

router = APIRouter(prefix="/api/v1")


@router.get("/agents", tags=["Agents"])
def list_agents():
    """List all available agents with their capabilities."""
    agents = AgentRegistry.list_all()
    return {"agents": agents, "total": len(agents)}


@router.get("/agents/{agent_name}", tags=["Agents"])
def get_agent(agent_name: str):
    """Get details for a specific agent."""
    agent_cls = AgentRegistry.get(agent_name)
    if not agent_cls:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    return agent_cls().to_dict()


@router.post("/agents/{agent_name}/execute", tags=["Agents"])
async def execute_agent(agent_name: str, request: AgentExecuteRequest):
    """Execute a single agent with given input data."""
    engine = get_engine()
    result = await engine.execute_single_agent(agent_name, request.input_data)
    return {
        "agent": agent_name,
        "success": result.success,
        "output": result.output,
        "error": result.error,
        "tokens_used": result.tokens_used,
        "execution_time_ms": result.execution_time_ms,
        "logs": result.logs,
    }


@router.get("/workflows", tags=["Workflows"])
def list_workflows(db: Session = Depends(get_db)):
    """List all saved workflows."""
    workflows = db.query(WorkflowModel).order_by(WorkflowModel.created_at.desc()).all()
    return {
        "workflows": [
            {
                "id": w.id, "name": w.name, "description": w.description,
                "node_count": len(w.nodes_json),
                "created_at": w.created_at.isoformat(),
            }
            for w in workflows
        ],
        "total": len(workflows),
    }


@router.post("/workflows", tags=["Workflows"])
def create_workflow(request: CreateWorkflowRequest, db: Session = Depends(get_db)):
    """Create a new workflow definition."""
    workflow = WorkflowModel(
        name=request.name,
        description=request.description,
        nodes_json=[n.model_dump() for n in request.nodes],
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return {
        "id": workflow.id,
        "name": workflow.name,
        "description": workflow.description,
        "nodes": workflow.nodes_json,
        "created_at": workflow.created_at.isoformat(),
    }


@router.get("/workflows/{workflow_id}", tags=["Workflows"])
def get_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """Get workflow details."""
    workflow = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {
        "id": workflow.id,
        "name": workflow.name,
        "description": workflow.description,
        "nodes": workflow.nodes_json,
        "created_at": workflow.created_at.isoformat(),
    }


@router.post("/workflows/{workflow_id}/execute", tags=["Workflows"])
async def execute_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """Execute a saved workflow."""
    wf_model = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
    if not wf_model:
        raise HTTPException(status_code=404, detail="Workflow not found")

    nodes = [
        WorkflowNode(
            id=n["id"],
            agent_name=n["agent_name"],
            input_data=n.get("input_data", {}),
            depends_on=n.get("depends_on", []),
            input_mapping=n.get("input_mapping", {}),
        )
        for n in wf_model.nodes_json
    ]
    workflow_def = WorkflowDefinition(
        id=wf_model.id, name=wf_model.name,
        description=wf_model.description, nodes=nodes,
    )

    engine = get_engine()
    state = await engine.execute_workflow(workflow_def)

    execution = ExecutionModel(
        id=state.execution_id,
        workflow_id=workflow_id,
        workflow_name=wf_model.name,
        status=state.status,
        result_json=state.to_dict(),
        total_time_ms=(state.completed_at - state.started_at) * 1000 if state.started_at and state.completed_at else None,
    )
    db.add(execution)
    db.commit()

    return state.to_dict()


@router.get("/executions", tags=["Executions"])
def list_executions(db: Session = Depends(get_db)):
    """List execution history."""
    executions = db.query(ExecutionModel).order_by(ExecutionModel.created_at.desc()).limit(50).all()
    return {
        "executions": [
            {
                "id": e.id, "workflow_id": e.workflow_id,
                "workflow_name": e.workflow_name, "status": e.status,
                "total_time_ms": e.total_time_ms,
                "created_at": e.created_at.isoformat(),
            }
            for e in executions
        ],
    }


@router.get("/executions/{execution_id}", tags=["Executions"])
def get_execution(execution_id: str, db: Session = Depends(get_db)):
    """Get detailed execution results."""
    engine = get_engine()
    state = engine.get_execution(execution_id)
    if state:
        return state.to_dict()

    execution = db.query(ExecutionModel).filter(ExecutionModel.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution.result_json


@router.get("/tools", tags=["Tools"])
def list_tools():
    """List all available tools that agents can use."""
    return {"tools": ToolRegistry.list_all()}


PREBUILT_WORKFLOWS = [
    {
        "id": "content-pipeline",
        "name": "Content Pipeline",
        "description": "Research a topic, analyze findings, and generate a polished article.",
        "nodes": [
            {"id": "research", "agent_name": "research", "input_data": {"query": ""}, "depends_on": []},
            {"id": "analyze", "agent_name": "analyst", "input_data": {"data": ""}, "depends_on": ["research"],
             "input_mapping": {"data": "research.summary"}},
            {"id": "write", "agent_name": "writer", "input_data": {"prompt": "", "format": "article"},
             "depends_on": ["analyze"], "input_mapping": {"prompt": "analyze.analysis"}},
        ],
    },
    {
        "id": "code-review",
        "name": "Code Review Pipeline",
        "description": "Generate code, then analyze and refine it.",
        "nodes": [
            {"id": "generate", "agent_name": "coder", "input_data": {"task": ""}, "depends_on": []},
            {"id": "review", "agent_name": "analyst", "input_data": {"data": ""},
             "depends_on": ["generate"], "input_mapping": {"data": "generate.code"}},
        ],
    },
    {
        "id": "research-report",
        "name": "Research Report",
        "description": "Coordinate a research project with task decomposition, research, and report writing.",
        "nodes": [
            {"id": "plan", "agent_name": "coordinator", "input_data": {"task": ""}, "depends_on": []},
            {"id": "research", "agent_name": "research", "input_data": {"query": ""},
             "depends_on": ["plan"], "input_mapping": {"query": "plan.task"}},
            {"id": "report", "agent_name": "writer",
             "input_data": {"prompt": "", "format": "report", "tone": "professional"},
             "depends_on": ["research"], "input_mapping": {"prompt": "research.summary"}},
        ],
    },
]


@router.get("/workflows/prebuilt/list", tags=["Workflows"])
def list_prebuilt_workflows():
    """List pre-built workflow templates."""
    return {"workflows": PREBUILT_WORKFLOWS}
