"""Tests for AgentForge agent system and workflow engine."""

import pytest
import asyncio

from app.agents.base import AgentRegistry, AgentCapability, AgentConfig
from app.agents import builtin  # noqa: F401
from app.agents.tools import ToolRegistry
from app.engine.workflow import (
    WorkflowEngine, WorkflowDefinition, WorkflowNode, NodeStatus,
)


class TestAgentRegistry:
    def test_agents_registered(self):
        agents = AgentRegistry.list_all()
        names = {a["name"] for a in agents}
        assert "research" in names
        assert "writer" in names
        assert "analyst" in names
        assert "coder" in names
        assert "coordinator" in names

    def test_create_agent(self):
        agent = AgentRegistry.create("research")
        assert agent is not None
        assert agent.name == "research"
        assert AgentCapability.WEB_SEARCH in agent.capabilities

    def test_unknown_agent(self):
        agent = AgentRegistry.create("nonexistent")
        assert agent is None


class TestToolRegistry:
    def test_tools_registered(self):
        tools = ToolRegistry.list_all()
        names = {t["name"] for t in tools}
        assert "web_fetch" in names
        assert "text_transform" in names
        assert "json_parse" in names
        assert "csv_analyze" in names

    def test_text_transform(self):
        tool = ToolRegistry.get("text_transform")
        assert tool is not None
        result = asyncio.get_event_loop().run_until_complete(
            tool.invoke(text="hello world", operation="uppercase")
        )
        assert result.success
        assert result.data["result"] == "HELLO WORLD"

    def test_json_parse_valid(self):
        tool = ToolRegistry.get("json_parse")
        result = asyncio.get_event_loop().run_until_complete(
            tool.invoke(text='{"key": "value"}')
        )
        assert result.success
        assert result.data["parsed"]["key"] == "value"

    def test_json_parse_invalid(self):
        tool = ToolRegistry.get("json_parse")
        result = asyncio.get_event_loop().run_until_complete(
            tool.invoke(text='not json')
        )
        assert not result.success

    def test_csv_analyze(self):
        tool = ToolRegistry.get("csv_analyze")
        csv = "name,value\nA,10\nB,20\nC,30"
        result = asyncio.get_event_loop().run_until_complete(
            tool.invoke(csv_text=csv)
        )
        assert result.success
        assert result.data["row_count"] == 3
        assert "value" in result.data["numeric_summary"]


class TestAgentExecution:
    def test_writer_agent(self):
        agent = AgentRegistry.create("writer")
        result = asyncio.get_event_loop().run_until_complete(
            agent.execute({"prompt": "Write a greeting", "tone": "friendly", "format": "email"})
        )
        assert result.success
        assert "content" in result.output
        assert result.output["word_count"] > 0

    def test_coder_agent(self):
        agent = AgentRegistry.create("coder")
        result = asyncio.get_event_loop().run_until_complete(
            agent.execute({"task": "Create a hello world function", "language": "python"})
        )
        assert result.success
        assert "code" in result.output

    def test_coordinator_agent(self):
        agent = AgentRegistry.create("coordinator")
        result = asyncio.get_event_loop().run_until_complete(
            agent.execute({"task": "Build a website for a restaurant"})
        )
        assert result.success
        assert "plan" in result.output
        assert len(result.output["plan"]) > 0


class TestWorkflowEngine:
    def test_simple_workflow(self):
        nodes = [
            WorkflowNode(id="step1", agent_name="writer", input_data={"prompt": "Hello world"}),
        ]
        workflow = WorkflowDefinition(id="test-1", name="Simple", description="Test", nodes=nodes)

        engine = WorkflowEngine()
        state = asyncio.get_event_loop().run_until_complete(engine.execute_workflow(workflow))
        assert state.status == "completed"
        assert state.nodes["step1"].status == NodeStatus.COMPLETED

    def test_chained_workflow(self):
        nodes = [
            WorkflowNode(id="step1", agent_name="writer", input_data={"prompt": "Write about AI"}),
            WorkflowNode(id="step2", agent_name="analyst", input_data={"data": ""},
                        depends_on=["step1"], input_mapping={"data": "step1.content"}),
        ]
        workflow = WorkflowDefinition(id="test-2", name="Chain", description="Test", nodes=nodes)

        engine = WorkflowEngine()
        state = asyncio.get_event_loop().run_until_complete(engine.execute_workflow(workflow))
        assert state.status == "completed"

    def test_validation_unknown_agent(self):
        nodes = [
            WorkflowNode(id="step1", agent_name="nonexistent_agent", input_data={}),
        ]
        workflow = WorkflowDefinition(id="test-3", name="Bad", description="Test", nodes=nodes)
        errors = workflow.validate()
        assert len(errors) > 0

    def test_validation_missing_dependency(self):
        nodes = [
            WorkflowNode(id="step1", agent_name="writer", input_data={}, depends_on=["missing"]),
        ]
        workflow = WorkflowDefinition(id="test-4", name="Bad", description="Test", nodes=nodes)
        errors = workflow.validate()
        assert len(errors) > 0

    def test_execution_order_parallel(self):
        nodes = [
            WorkflowNode(id="a", agent_name="writer", input_data={"prompt": "A"}),
            WorkflowNode(id="b", agent_name="writer", input_data={"prompt": "B"}),
            WorkflowNode(id="c", agent_name="writer", input_data={"prompt": "C"}, depends_on=["a", "b"]),
        ]
        workflow = WorkflowDefinition(id="test-5", name="Parallel", description="Test", nodes=nodes)
        layers = workflow.get_execution_order()
        assert len(layers) == 2
        assert set(layers[0]) == {"a", "b"}
        assert layers[1] == ["c"]
