from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    current_agent: Optional[str]
    task_type: Optional[str]
    intermediate_results: dict
    user_context: dict
    session_id: str
    agent_thoughts: list[str]
