from pydantic import BaseModel, Field


class AgentExecuteRequest(BaseModel):
    input_data: dict = Field(..., description="Input data for the agent")


class WorkflowNodeSchema(BaseModel):
    id: str = Field(..., description="Unique node ID")
    agent_name: str = Field(..., description="Agent to execute")
    input_data: dict = Field(default_factory=dict, description="Static input data")
    depends_on: list[str] = Field(default_factory=list, description="Node IDs this depends on")
    input_mapping: dict[str, str] = Field(
        default_factory=dict,
        description="Map input keys from other node outputs. Format: {target_key: 'source_node.output_key'}",
    )


class CreateWorkflowRequest(BaseModel):
    name: str = Field(..., description="Workflow name")
    description: str = Field(default="", description="Workflow description")
    nodes: list[WorkflowNodeSchema] = Field(..., description="Workflow nodes (DAG)")


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str
    nodes: list[dict]
    created_at: str


class ExecutionResponse(BaseModel):
    execution_id: str
    workflow_id: str
    workflow_name: str
    status: str
    nodes: dict
    started_at: float | None
    completed_at: float | None
    total_time_ms: float | None
    logs: list[str]
