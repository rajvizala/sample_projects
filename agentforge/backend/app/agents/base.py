"""
Base agent class and agent registry.
All agents inherit from BaseAgent and register themselves in the global registry.
"""

from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from typing import Any


class AgentCapability(str, Enum):
    TEXT_GENERATION = "text_generation"
    TEXT_ANALYSIS = "text_analysis"
    DATA_ANALYSIS = "data_analysis"
    CODE_GENERATION = "code_generation"
    WEB_SEARCH = "web_search"
    SUMMARIZATION = "summarization"
    TASK_DECOMPOSITION = "task_decomposition"
    TRANSFORMATION = "transformation"


@dataclass
class AgentConfig:
    max_retries: int = 3
    timeout_seconds: int = 60
    temperature: float = 0.7
    max_tokens: int = 2000


@dataclass
class AgentResult:
    success: bool
    output: dict[str, Any]
    error: str | None = None
    tokens_used: int = 0
    execution_time_ms: float = 0
    logs: list[str] = field(default_factory=list)


class BaseAgent(ABC):
    """Base class for all agents in AgentForge."""

    name: str = "base_agent"
    description: str = "Base agent"
    capabilities: list[AgentCapability] = []
    required_inputs: list[str] = []
    output_schema: dict[str, str] = {}

    def __init__(self, config: AgentConfig | None = None):
        self.config = config or AgentConfig()
        self.memory: list[dict] = []

    @abstractmethod
    async def execute(self, input_data: dict, context: dict | None = None) -> AgentResult:
        """Execute the agent with given input and optional context."""
        pass

    def add_memory(self, key: str, value: Any):
        self.memory.append({"key": key, "value": value})

    def get_memory(self, key: str) -> Any | None:
        for item in reversed(self.memory):
            if item["key"] == key:
                return item["value"]
        return None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": [c.value for c in self.capabilities],
            "required_inputs": self.required_inputs,
            "output_schema": self.output_schema,
            "config": {
                "max_retries": self.config.max_retries,
                "timeout_seconds": self.config.timeout_seconds,
            },
        }


class AgentRegistry:
    """Global registry for all available agents."""

    _agents: dict[str, type[BaseAgent]] = {}

    @classmethod
    def register(cls, agent_class: type[BaseAgent]):
        cls._agents[agent_class.name] = agent_class
        return agent_class

    @classmethod
    def get(cls, name: str) -> type[BaseAgent] | None:
        return cls._agents.get(name)

    @classmethod
    def list_all(cls) -> list[dict]:
        return [cls._agents[name]().to_dict() for name in sorted(cls._agents)]

    @classmethod
    def create(cls, name: str, config: AgentConfig | None = None) -> BaseAgent | None:
        agent_class = cls._agents.get(name)
        if agent_class:
            return agent_class(config)
        return None
