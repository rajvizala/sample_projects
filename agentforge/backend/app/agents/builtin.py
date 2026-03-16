"""
Built-in agent implementations for AgentForge.
Each agent is a specialized worker that can be composed into workflows.
"""

import time
import re
import json

from app.agents.base import (
    BaseAgent, AgentCapability, AgentConfig, AgentResult, AgentRegistry,
)
from app.agents.tools import ToolRegistry
from app.core.config import get_settings


async def _call_llm(prompt: str, system: str = "", temperature: float = 0.7) -> dict:
    """Call LLM API (Gemini or fallback to rule-based)."""
    settings = get_settings()

    if settings.gemini_api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel("gemini-2.0-flash")
            full_prompt = f"{system}\n\n{prompt}" if system else prompt
            response = model.generate_content(full_prompt)
            return {"text": response.text, "tokens": len(response.text.split()), "source": "gemini"}
        except Exception as e:
            return {"text": f"LLM call failed: {e}", "tokens": 0, "source": "error"}

    return {
        "text": _rule_based_fallback(prompt, system),
        "tokens": 0,
        "source": "rule_based_fallback",
    }


def _rule_based_fallback(prompt: str, system: str) -> str:
    """Deterministic fallback when no LLM API is configured."""
    prompt_lower = prompt.lower()

    if "summarize" in prompt_lower or "summary" in prompt_lower:
        sentences = re.split(r'[.!?]+', prompt)
        key_sentences = [s.strip() for s in sentences if len(s.strip()) > 30][:3]
        return "Summary: " + ". ".join(key_sentences) + "." if key_sentences else "Summary: Content too brief to summarize."

    if "analyze" in prompt_lower or "analysis" in prompt_lower:
        words = prompt.split()
        return (
            f"Analysis of input ({len(words)} words): "
            f"The content covers multiple topics. Key themes identified include "
            f"the primary subject matter discussed in the text. "
            f"Further analysis would require more specific parameters."
        )

    if "write" in prompt_lower or "generate" in prompt_lower or "create" in prompt_lower:
        topic = prompt[:100].replace("write", "").replace("generate", "").replace("create", "").strip()
        return (
            f"Generated content about {topic[:50]}:\n\n"
            f"This is a placeholder for AI-generated content. "
            f"When configured with a Gemini API key, this agent produces "
            f"high-quality, contextually relevant text based on the given prompt. "
            f"The content would be tailored to the specific requirements and tone requested."
        )

    if "code" in prompt_lower or "function" in prompt_lower or "implement" in prompt_lower:
        return (
            '```python\ndef process(data):\n    """Process the input data."""\n'
            '    result = []\n    for item in data:\n        result.append(transform(item))\n'
            '    return result\n```\n\n'
            'Note: This is a placeholder. Connect a Gemini API key for real code generation.'
        )

    if "break" in prompt_lower or "decompose" in prompt_lower or "plan" in prompt_lower:
        return json.dumps({
            "tasks": [
                {"step": 1, "action": "Research and gather requirements", "agent": "research"},
                {"step": 2, "action": "Analyze the collected data", "agent": "analyst"},
                {"step": 3, "action": "Generate output based on analysis", "agent": "writer"},
                {"step": 4, "action": "Review and refine the results", "agent": "writer"},
            ]
        }, indent=2)

    return (
        f"Processed input ({len(prompt)} chars). "
        f"Configure GEMINI_API_KEY for intelligent AI responses. "
        f"Without an API key, agents use rule-based fallback logic."
    )


@AgentRegistry.register
class ResearchAgent(BaseAgent):
    name = "research"
    description = "Researches topics by fetching web content, extracting key information, and producing structured summaries."
    capabilities = [AgentCapability.WEB_SEARCH, AgentCapability.SUMMARIZATION, AgentCapability.TEXT_ANALYSIS]
    required_inputs = ["query"]
    output_schema = {"summary": "str", "sources": "list", "key_points": "list"}

    async def execute(self, input_data: dict, context: dict | None = None) -> AgentResult:
        start = time.time()
        query = input_data.get("query", "")
        logs = [f"Starting research on: {query}"]

        sources = []
        url = input_data.get("url")
        if url:
            tool = ToolRegistry.get("web_fetch")
            if tool:
                result = await tool.invoke(url=url)
                if result.success:
                    sources.append({"url": url, "content": result.data["content"][:1000]})
                    logs.append(f"Fetched content from {url}")

        source_text = "\n".join(s["content"] for s in sources) if sources else ""
        prompt = f"Research query: {query}\n\nAvailable sources:\n{source_text}\n\nProvide a comprehensive research summary with key points."
        llm_result = await _call_llm(prompt, system="You are a research analyst. Provide thorough, factual analysis.")

        elapsed = (time.time() - start) * 1000
        logs.append(f"Research complete in {elapsed:.0f}ms")

        return AgentResult(
            success=True,
            output={
                "summary": llm_result["text"],
                "sources": [s["url"] for s in sources],
                "key_points": _extract_key_points(llm_result["text"]),
                "llm_source": llm_result["source"],
            },
            tokens_used=llm_result["tokens"],
            execution_time_ms=elapsed,
            logs=logs,
        )


@AgentRegistry.register
class WriterAgent(BaseAgent):
    name = "writer"
    description = "Generates written content including articles, emails, reports, and marketing copy."
    capabilities = [AgentCapability.TEXT_GENERATION]
    required_inputs = ["prompt"]
    output_schema = {"content": "str", "word_count": "int"}

    async def execute(self, input_data: dict, context: dict | None = None) -> AgentResult:
        start = time.time()
        prompt = input_data.get("prompt", "")
        tone = input_data.get("tone", "professional")
        format_type = input_data.get("format", "article")

        context_text = ""
        if context and context.get("previous_output"):
            context_text = f"\n\nContext from previous step:\n{context['previous_output'][:1000]}"

        full_prompt = (
            f"Write a {format_type} with a {tone} tone.\n\n"
            f"Topic/Instructions: {prompt}{context_text}\n\n"
            f"Generate high-quality, well-structured content."
        )

        llm_result = await _call_llm(full_prompt, system=f"You are an expert {format_type} writer. Tone: {tone}.")
        content = llm_result["text"]
        elapsed = (time.time() - start) * 1000

        return AgentResult(
            success=True,
            output={
                "content": content,
                "word_count": len(content.split()),
                "format": format_type,
                "tone": tone,
                "llm_source": llm_result["source"],
            },
            tokens_used=llm_result["tokens"],
            execution_time_ms=elapsed,
            logs=[f"Generated {len(content.split())} words in {elapsed:.0f}ms"],
        )


@AgentRegistry.register
class DataAnalystAgent(BaseAgent):
    name = "analyst"
    description = "Analyzes structured data (CSV/JSON), computes statistics, identifies patterns, and generates insights."
    capabilities = [AgentCapability.DATA_ANALYSIS, AgentCapability.TEXT_ANALYSIS]
    required_inputs = ["data"]
    output_schema = {"analysis": "str", "statistics": "dict", "insights": "list"}

    async def execute(self, input_data: dict, context: dict | None = None) -> AgentResult:
        start = time.time()
        data = input_data.get("data", "")
        logs = ["Starting data analysis"]

        stats = {}
        csv_tool = ToolRegistry.get("csv_analyze")
        if csv_tool and "," in data:
            result = await csv_tool.invoke(csv_text=data)
            if result.success:
                stats = result.data
                logs.append(f"Parsed {stats.get('row_count', 0)} rows with {len(stats.get('columns', []))} columns")

        prompt = f"Analyze this data and provide insights:\n\n{data[:2000]}\n\nStatistics: {json.dumps(stats, indent=2)}"
        llm_result = await _call_llm(prompt, system="You are a data analyst. Provide clear, actionable insights.")
        elapsed = (time.time() - start) * 1000

        return AgentResult(
            success=True,
            output={
                "analysis": llm_result["text"],
                "statistics": stats,
                "insights": _extract_key_points(llm_result["text"]),
                "llm_source": llm_result["source"],
            },
            tokens_used=llm_result["tokens"],
            execution_time_ms=elapsed,
            logs=logs,
        )


@AgentRegistry.register
class CodeAgent(BaseAgent):
    name = "coder"
    description = "Generates, reviews, and transforms code. Supports Python, JavaScript, and more."
    capabilities = [AgentCapability.CODE_GENERATION, AgentCapability.TEXT_ANALYSIS]
    required_inputs = ["task"]
    output_schema = {"code": "str", "language": "str", "explanation": "str"}

    async def execute(self, input_data: dict, context: dict | None = None) -> AgentResult:
        start = time.time()
        task = input_data.get("task", "")
        language = input_data.get("language", "python")

        prompt = (
            f"Task: {task}\nLanguage: {language}\n\n"
            f"Generate clean, well-documented code. Include brief explanation."
        )
        llm_result = await _call_llm(prompt, system=f"You are an expert {language} developer.")

        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', llm_result["text"], re.DOTALL)
        code = code_blocks[0].strip() if code_blocks else llm_result["text"]

        elapsed = (time.time() - start) * 1000
        return AgentResult(
            success=True,
            output={
                "code": code,
                "language": language,
                "explanation": llm_result["text"],
                "llm_source": llm_result["source"],
            },
            tokens_used=llm_result["tokens"],
            execution_time_ms=elapsed,
            logs=[f"Code generated in {elapsed:.0f}ms"],
        )


@AgentRegistry.register
class CoordinatorAgent(BaseAgent):
    name = "coordinator"
    description = "Meta-agent that decomposes complex tasks into sub-tasks and assigns them to appropriate agents."
    capabilities = [AgentCapability.TASK_DECOMPOSITION]
    required_inputs = ["task"]
    output_schema = {"plan": "list", "reasoning": "str"}

    async def execute(self, input_data: dict, context: dict | None = None) -> AgentResult:
        start = time.time()
        task = input_data.get("task", "")

        available_agents = AgentRegistry.list_all()
        agent_desc = "\n".join(f"- {a['name']}: {a['description']}" for a in available_agents if a["name"] != "coordinator")

        prompt = (
            f"Break down this task into steps and assign each to the best agent:\n\n"
            f"Task: {task}\n\n"
            f"Available agents:\n{agent_desc}\n\n"
            f"Return a JSON plan with steps, each having: step_number, description, agent_name, input_mapping"
        )
        llm_result = await _call_llm(prompt, system="You are a task coordinator. Create efficient execution plans.")

        try:
            plan = json.loads(llm_result["text"])
            if isinstance(plan, dict):
                plan = plan.get("tasks", plan.get("steps", []))
        except json.JSONDecodeError:
            plan = [
                {"step": 1, "description": "Research the topic", "agent": "research"},
                {"step": 2, "description": "Analyze findings", "agent": "analyst"},
                {"step": 3, "description": "Generate final output", "agent": "writer"},
            ]

        elapsed = (time.time() - start) * 1000
        return AgentResult(
            success=True,
            output={
                "plan": plan,
                "reasoning": llm_result["text"],
                "task": task,
                "llm_source": llm_result["source"],
            },
            tokens_used=llm_result["tokens"],
            execution_time_ms=elapsed,
            logs=[f"Task decomposed into {len(plan)} steps in {elapsed:.0f}ms"],
        )


def _extract_key_points(text: str) -> list[str]:
    """Extract key points from text using simple heuristics."""
    points = []
    for line in text.split("\n"):
        line = line.strip()
        if line and (line.startswith(("-", "*", "1", "2", "3", "4", "5")) or len(line) > 20):
            clean = re.sub(r'^[-*\d.)\s]+', '', line).strip()
            if len(clean) > 15:
                points.append(clean)
    return points[:10] if points else [text[:200]]
