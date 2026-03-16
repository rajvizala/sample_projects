import json
from typing import Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from .state import AgentState
from .tools import RESEARCH_TOOLS, ANALYTICS_TOOLS, CONTENT_TOOLS, CUSTOMER_TOOLS, ALL_TOOLS
from ..config import get_settings

settings = get_settings()

ORCHESTRATOR_SYSTEM = """You are the AgentOS orchestrator — the central intelligence for a solopreneur's AI-powered business.

Your job is to analyze what the user needs and produce a JSON routing decision. The specialized agents you can delegate to are:

- research: Market analysis, competitor research, trend identification, opportunity mapping
- content: Blog posts, email campaigns, social media copy, landing pages, product descriptions  
- analytics: Business metric analysis, KPI interpretation, growth forecasting, performance insights
- customer: Customer message drafting, support responses, complaint handling, follow-up emails

Analyze the user's message and respond with EXACTLY this JSON (no markdown, no explanation):
{
  "agent": "<one of: research | content | analytics | customer | general>",
  "task_description": "<concise description of the specific task>",
  "key_requirements": ["<requirement 1>", "<requirement 2>"]
}

If the request is a general business question or doesn't fit a specialized agent, use "general" and you will handle it directly."""

AGENT_SYSTEMS = {
    "research": """You are a senior market research analyst inside AgentOS. You have deep expertise in competitive intelligence, market sizing, and trend analysis.

Use your available tools to gather data, then synthesize it into actionable strategic insights. Be specific with numbers when possible. Format your output as a structured analysis with clear sections.

Business context from the user:
{business_context}""",

    "content": """You are a world-class content strategist and copywriter inside AgentOS. You create high-converting, engaging content that drives real business results.

Use your tools to create a structured content plan, then generate compelling, platform-appropriate copy. Focus on hooks, clarity, and CTAs.

Business context from the user:
{business_context}""",

    "analytics": """You are a data-driven business analyst inside AgentOS. You turn raw metrics into clear narratives that drive decisions.

Use your tools to analyze the data, identify patterns, surface anomalies, and generate prioritized recommendations. Be direct about what the numbers mean.

Business context from the user:
{business_context}""",

    "customer": """You are an expert customer success manager inside AgentOS. You craft responses that resolve issues, retain customers, and turn complaints into loyalty.

Use your tools to analyze the customer's message, then draft a response that is empathetic, solution-oriented, and professional.

Business context from the user:
{business_context}""",

    "general": """You are AgentOS, a sophisticated AI business advisor for solopreneurs. You provide expert guidance on strategy, operations, growth, and execution.

Be direct, specific, and actionable. Avoid generic advice. Ground your recommendations in first principles.

Business context from the user:
{business_context}"""
}


def build_llm(streaming: bool = True) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        streaming=streaming,
        temperature=0.7,
    )


def orchestrator_node(state: AgentState) -> AgentState:
    llm = build_llm(streaming=False)
    messages = state["messages"]
    last_human = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
    if not last_human:
        return {**state, "current_agent": "general", "task_type": "general"}

    response = llm.invoke([
        SystemMessage(content=ORCHESTRATOR_SYSTEM),
        HumanMessage(content=last_human.content)
    ])

    try:
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        routing = json.loads(raw.strip())
        agent = routing.get("agent", "general")
        task_desc = routing.get("task_description", "")
        thoughts = state.get("agent_thoughts", [])
        thoughts.append(f"Routing to {agent} agent: {task_desc}")
        return {
            **state,
            "current_agent": agent,
            "task_type": agent,
            "agent_thoughts": thoughts
        }
    except (json.JSONDecodeError, Exception):
        return {**state, "current_agent": "general", "task_type": "general"}


def route_after_orchestrator(state: AgentState) -> Literal["research", "content", "analytics", "customer", "general"]:
    agent = state.get("current_agent", "general")
    return agent if agent in ("research", "content", "analytics", "customer") else "general"


def _make_agent_node(agent_name: str, tools: list):
    tool_map = {t.name: t for t in tools}

    def agent_node(state: AgentState) -> AgentState:
        llm = build_llm(streaming=True)
        llm_with_tools = llm.bind_tools(tools) if tools else llm
        business_ctx = json.dumps(state.get("user_context", {}), indent=2)
        system = AGENT_SYSTEMS[agent_name].format(business_context=business_ctx)
        conversation = [SystemMessage(content=system)] + state["messages"]
        response = llm_with_tools.invoke(conversation)

        new_messages = [response]
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tc in response.tool_calls:
                tool_fn = tool_map.get(tc["name"])
                if tool_fn:
                    tool_result = tool_fn.invoke(tc["args"])
                    new_messages.append(ToolMessage(content=str(tool_result), tool_call_id=tc["id"]))
            followup = llm.invoke([SystemMessage(content=system)] + state["messages"] + new_messages)
            new_messages.append(followup)

        thoughts = state.get("agent_thoughts", [])
        thoughts.append(f"{agent_name} agent completed task")

        return {
            **state,
            "messages": new_messages,
            "agent_thoughts": thoughts
        }

    agent_node.__name__ = f"{agent_name}_node"
    return agent_node


def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("research", _make_agent_node("research", RESEARCH_TOOLS))
    workflow.add_node("content", _make_agent_node("content", CONTENT_TOOLS))
    workflow.add_node("analytics", _make_agent_node("analytics", ANALYTICS_TOOLS))
    workflow.add_node("customer", _make_agent_node("customer", CUSTOMER_TOOLS))
    workflow.add_node("general", _make_agent_node("general", []))

    workflow.set_entry_point("orchestrator")
    workflow.add_conditional_edges(
        "orchestrator",
        route_after_orchestrator,
        {
            "research": "research",
            "content": "content",
            "analytics": "analytics",
            "customer": "customer",
            "general": "general",
        }
    )
    for agent in ("research", "content", "analytics", "customer", "general"):
        workflow.add_edge(agent, END)

    return workflow.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
