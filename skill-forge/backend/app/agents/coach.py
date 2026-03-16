"""
Adaptive AI coaching agent using LangGraph for conversational learning.
"""
import json
from typing import AsyncIterator
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from ..config import get_settings
from ..graph import get_skill_graph

settings = get_settings()

COACH_SYSTEM = """You are SkillForge Coach — an expert AI upskilling trainer for software engineers and AI/ML practitioners.

Your teaching philosophy:
1. Be concrete and practical — always tie concepts to real-world code examples
2. Scaffold learning — start simple, build up complexity
3. Ask questions to check understanding
4. Give immediate, specific feedback on answers
5. Celebrate progress genuinely, but don't be sycophantic

Learner profile:
{learner_profile}

Current skill focus: {current_skill}
Skill description: {skill_description}

Guidelines:
- When explaining concepts, include a brief code snippet when relevant
- After explaining something, ask one specific follow-up question to test understanding
- When the learner demonstrates mastery, explicitly say "You've mastered this concept!" 
- Suggest the next skill to learn when appropriate
- Keep responses focused and under 300 words unless the learner asks for more depth
- Format code with triple backticks and language name

You have deep expertise in: Python, ML/DL, LLMs, RAG, LangChain, LangGraph, Vector Databases, MLOps, and AI agent systems."""

ASSESSMENT_SYSTEM = """You are a precise AI skills assessor. Evaluate the learner's response to an assessment question.

Skill being assessed: {skill_id}
Question asked: {question}
Learner's answer: {answer}

Respond with EXACTLY this JSON (no markdown):
{{
  "score": <0.0 to 1.0>,
  "level": "<novice|beginner|intermediate|advanced|expert>",
  "correct_concepts": ["<concept>"],
  "missing_concepts": ["<concept>"],
  "feedback": "<2-3 sentence specific feedback>",
  "next_question": "<a harder follow-up question if score > 0.6, or clarification if < 0.6>"
}}"""

ASSESSMENT_QUESTIONS = {
    "llm_basics": [
        "Explain what temperature does in LLM inference and when you'd set it near 0 vs near 1.",
        "What is a context window and why does it matter for RAG systems?",
        "Explain the difference between zero-shot and few-shot prompting with a concrete example.",
    ],
    "prompt_engineering": [
        "Write a chain-of-thought prompt for solving a multi-step math problem.",
        "What is the RISEN framework for prompting and when would you use it?",
        "How would you structure a system prompt for a customer support bot that handles refunds?",
    ],
    "rag_systems": [
        "What is the difference between sparse (BM25) and dense (embedding) retrieval? When would you use each?",
        "Walk me through how you would chunk a 200-page technical PDF for a RAG pipeline.",
        "What is re-ranking in RAG and why does it improve retrieval quality?",
    ],
    "langchain": [
        "What is a LangChain chain and how does it differ from a simple LLM call?",
        "Explain how memory works in LangChain and what ConversationBufferWindowMemory does.",
        "How would you add a custom tool to a LangChain agent?",
    ],
    "langgraph": [
        "What is a StateGraph in LangGraph and what problem does it solve over simple chains?",
        "Explain the difference between add_edge and add_conditional_edges in LangGraph.",
        "How does LangGraph handle state persistence across multiple agent invocations?",
    ],
    "vector_databases": [
        "Explain cosine similarity vs Euclidean distance for vector search — when does each matter?",
        "What is HNSW indexing and why is it commonly used in vector databases?",
        "How would you handle metadata filtering in a vector store for a multi-tenant RAG system?",
    ],
    "fine_tuning": [
        "What is LoRA and how does it reduce GPU memory requirements compared to full fine-tuning?",
        "When would you fine-tune a model vs just using better prompts?",
        "What is catastrophic forgetting and how do you mitigate it during fine-tuning?",
    ],
    "ai_agents": [
        "Explain the ReAct (Reason + Act) pattern for AI agents with an example.",
        "What is the difference between a tool-using agent and an autonomous agent?",
        "How would you prevent an AI agent from getting stuck in an infinite loop?",
    ],
    "ml_fundamentals": [
        "Explain the bias-variance tradeoff with a concrete example.",
        "What is cross-validation and why is it important to use it?",
        "Explain regularization (L1 vs L2) — what does each one do to model weights?",
    ],
}


def _build_llm(streaming: bool = True) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        streaming=streaming,
        temperature=0.7,
    )


async def stream_coaching_response(
    messages: list,
    skill_id: str,
    learner: dict
) -> AsyncIterator[str]:
    skill_graph = get_skill_graph()
    skill = skill_graph.get_skill(skill_id) or {}

    learner_profile = json.dumps({
        "name": learner.get("name", "Learner"),
        "role": learner.get("role", "Software Engineer"),
        "experience": learner.get("experience_level", "intermediate"),
        "mastered_skills": learner.get("mastered_skills", []),
        "xp_points": learner.get("xp_points", 0),
    }, indent=2)

    system = COACH_SYSTEM.format(
        learner_profile=learner_profile,
        current_skill=skill.get("label", skill_id),
        skill_description=skill.get("description", "")
    )

    lc_messages = [SystemMessage(content=system)]
    for msg in messages:
        if msg["role"] == "user":
            lc_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            lc_messages.append(AIMessage(content=msg["content"]))

    llm = _build_llm(streaming=True)
    async for chunk in llm.astream(lc_messages):
        if chunk.content:
            yield chunk.content


async def assess_skill_answer(skill_id: str, question: str, answer: str) -> dict:
    llm = _build_llm(streaming=False)
    system = ASSESSMENT_SYSTEM.format(
        skill_id=skill_id,
        question=question,
        answer=answer
    )
    response = llm.invoke([SystemMessage(content=system)])
    try:
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except (json.JSONDecodeError, Exception):
        return {
            "score": 0.5,
            "level": "intermediate",
            "correct_concepts": [],
            "missing_concepts": [],
            "feedback": "Good attempt! Let's explore this concept further.",
            "next_question": "Can you explain this in your own words?"
        }


def get_assessment_questions(skill_id: str) -> list[str]:
    default = [f"What do you know about {skill_id.replace('_', ' ')}?"]
    return ASSESSMENT_QUESTIONS.get(skill_id, default)
