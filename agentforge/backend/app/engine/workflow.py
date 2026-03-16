"""
DAG-based workflow engine for AgentForge.
Executes agent workflows with dependency resolution, parallel execution
of independent nodes, error handling, and state tracking.
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.agents.base import AgentRegistry, AgentResult


class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowNode:
    """A single node in the workflow DAG."""
    id: str
    agent_name: str
    input_data: dict
    depends_on: list[str] = field(default_factory=list)
    input_mapping: dict[str, str] = field(default_factory=dict)
    status: NodeStatus = NodeStatus.PENDING
    result: AgentResult | None = None
    started_at: float | None = None
    completed_at: float | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent_name": self.agent_name,
            "input_data": self.input_data,
            "depends_on": self.depends_on,
            "status": self.status.value,
            "result": {
                "success": self.result.success,
                "output": self.result.output,
                "error": self.result.error,
                "tokens_used": self.result.tokens_used,
                "execution_time_ms": self.result.execution_time_ms,
                "logs": self.result.logs,
            } if self.result else None,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


@dataclass
class WorkflowDefinition:
    """Definition of a workflow as a DAG of agent nodes."""
    id: str
    name: str
    description: str
    nodes: list[WorkflowNode]

    def validate(self) -> list[str]:
        """Validate the workflow DAG for cycles and missing dependencies."""
        errors = []
        node_ids = {n.id for n in self.nodes}

        for node in self.nodes:
            for dep in node.depends_on:
                if dep not in node_ids:
                    errors.append(f"Node '{node.id}' depends on unknown node '{dep}'")

            if AgentRegistry.get(node.agent_name) is None:
                errors.append(f"Node '{node.id}' references unknown agent '{node.agent_name}'")

        if self._has_cycle():
            errors.append("Workflow contains a cycle")

        return errors

    def _has_cycle(self) -> bool:
        """Detect cycles using DFS."""
        visited = set()
        rec_stack = set()
        adj = {n.id: n.depends_on for n in self.nodes}

        def dfs(node_id):
            visited.add(node_id)
            rec_stack.add(node_id)
            for dep in adj.get(node_id, []):
                if dep not in visited:
                    if dfs(dep):
                        return True
                elif dep in rec_stack:
                    return True
            rec_stack.discard(node_id)
            return False

        return any(dfs(n.id) for n in self.nodes if n.id not in visited)

    def get_execution_order(self) -> list[list[str]]:
        """Topological sort returning layers of parallelizable nodes."""
        in_degree = {n.id: len(n.depends_on) for n in self.nodes}
        adj = {}
        for n in self.nodes:
            for dep in n.depends_on:
                adj.setdefault(dep, []).append(n.id)

        layers = []
        remaining = set(in_degree.keys())

        while remaining:
            layer = [nid for nid in remaining if in_degree[nid] == 0]
            if not layer:
                break
            layers.append(layer)
            for nid in layer:
                remaining.discard(nid)
                for child in adj.get(nid, []):
                    in_degree[child] -= 1

        return layers


@dataclass
class ExecutionState:
    """Tracks the state of a workflow execution."""
    execution_id: str
    workflow_id: str
    workflow_name: str
    status: str = "pending"
    nodes: dict[str, WorkflowNode] = field(default_factory=dict)
    started_at: float | None = None
    completed_at: float | None = None
    logs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "status": self.status,
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_time_ms": (self.completed_at - self.started_at) * 1000 if self.started_at and self.completed_at else None,
            "logs": self.logs,
        }


class WorkflowEngine:
    """Executes workflow DAGs with parallel node execution."""

    def __init__(self):
        self.executions: dict[str, ExecutionState] = {}
        self._listeners: dict[str, list] = {}

    async def execute_workflow(
        self, workflow: WorkflowDefinition, callback=None,
    ) -> ExecutionState:
        errors = workflow.validate()
        if errors:
            state = ExecutionState(
                execution_id=str(uuid.uuid4()),
                workflow_id=workflow.id,
                workflow_name=workflow.name,
                status="failed",
                logs=[f"Validation error: {e}" for e in errors],
            )
            self.executions[state.execution_id] = state
            return state

        state = ExecutionState(
            execution_id=str(uuid.uuid4()),
            workflow_id=workflow.id,
            workflow_name=workflow.name,
            status="running",
            nodes={n.id: n for n in workflow.nodes},
            started_at=time.time(),
        )
        self.executions[state.execution_id] = state
        state.logs.append(f"Workflow '{workflow.name}' started")

        if callback:
            await callback(state)

        layers = workflow.get_execution_order()

        for layer_idx, layer in enumerate(layers):
            state.logs.append(f"Executing layer {layer_idx + 1}: {layer}")

            tasks = []
            for node_id in layer:
                node = state.nodes[node_id]
                tasks.append(self._execute_node(node, state, callback))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for node_id, result in zip(layer, results):
                if isinstance(result, Exception):
                    state.nodes[node_id].status = NodeStatus.FAILED
                    state.nodes[node_id].result = AgentResult(
                        success=False, output={}, error=str(result),
                    )
                    state.logs.append(f"Node '{node_id}' failed with exception: {result}")

            failed = [nid for nid in layer if state.nodes[nid].status == NodeStatus.FAILED]
            if failed:
                for remaining_node in state.nodes.values():
                    if remaining_node.status == NodeStatus.PENDING:
                        remaining_node.status = NodeStatus.SKIPPED
                state.status = "failed"
                state.completed_at = time.time()
                state.logs.append(f"Workflow failed due to node failures: {failed}")
                if callback:
                    await callback(state)
                return state

        state.status = "completed"
        state.completed_at = time.time()
        total_ms = (state.completed_at - state.started_at) * 1000
        state.logs.append(f"Workflow completed in {total_ms:.0f}ms")
        if callback:
            await callback(state)
        return state

    async def _execute_node(
        self, node: WorkflowNode, state: ExecutionState, callback=None,
    ):
        """Execute a single workflow node."""
        node.status = NodeStatus.RUNNING
        node.started_at = time.time()
        state.logs.append(f"Node '{node.id}' ({node.agent_name}) started")

        if callback:
            await callback(state)

        input_data = dict(node.input_data)
        for target_key, source_spec in node.input_mapping.items():
            parts = source_spec.split(".")
            if len(parts) == 2:
                source_node_id, source_key = parts
                source_node = state.nodes.get(source_node_id)
                if source_node and source_node.result and source_node.result.success:
                    input_data[target_key] = source_node.result.output.get(source_key, "")

        context = {}
        for dep_id in node.depends_on:
            dep_node = state.nodes.get(dep_id)
            if dep_node and dep_node.result:
                context["previous_output"] = str(dep_node.result.output)[:1000]

        agent = AgentRegistry.create(node.agent_name)
        if not agent:
            node.status = NodeStatus.FAILED
            node.result = AgentResult(success=False, output={}, error=f"Agent '{node.agent_name}' not found")
            return

        try:
            result = await agent.execute(input_data, context)
            node.result = result
            node.status = NodeStatus.COMPLETED if result.success else NodeStatus.FAILED
        except Exception as e:
            node.result = AgentResult(success=False, output={}, error=str(e))
            node.status = NodeStatus.FAILED

        node.completed_at = time.time()
        elapsed = (node.completed_at - node.started_at) * 1000
        state.logs.append(f"Node '{node.id}' {node.status.value} in {elapsed:.0f}ms")

        if callback:
            await callback(state)

    async def execute_single_agent(self, agent_name: str, input_data: dict) -> AgentResult:
        """Execute a single agent without a workflow."""
        agent = AgentRegistry.create(agent_name)
        if not agent:
            return AgentResult(success=False, output={}, error=f"Agent '{agent_name}' not found")
        return await agent.execute(input_data)

    def get_execution(self, execution_id: str) -> ExecutionState | None:
        return self.executions.get(execution_id)

    def list_executions(self, limit: int = 50) -> list[dict]:
        execs = sorted(self.executions.values(), key=lambda e: e.started_at or 0, reverse=True)
        return [e.to_dict() for e in execs[:limit]]


_engine: WorkflowEngine | None = None


def get_engine() -> WorkflowEngine:
    global _engine
    if _engine is None:
        _engine = WorkflowEngine()
    return _engine
