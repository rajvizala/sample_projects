import json
import uuid
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

from ..database import get_db
from ..models import Session, Message
from ..agents import get_graph
from ..cache import cache_get, cache_set, make_cache_key

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: str


async def stream_agent_response(
    message: str,
    session_id: str,
    history: list,
    business_context: dict,
    db: AsyncSession
) -> AsyncIterator[str]:
    cache_key = make_cache_key("chat", {"msg": message, "ctx": business_context})
    cached = await cache_get(cache_key)
    if cached:
        agent = cached.get("agent", "general")
        thoughts = cached.get("thoughts", [])
        for thought in thoughts:
            yield f"data: {json.dumps({'type': 'thought', 'content': thought, 'agent': agent})}\n\n"
        yield f"data: {json.dumps({'type': 'agent', 'agent': agent})}\n\n"
        content = cached.get("content", "")
        chunk_size = 30
        for i in range(0, len(content), chunk_size):
            yield f"data: {json.dumps({'type': 'token', 'content': content[i:i+chunk_size]})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'agent': agent})}\n\n"
        return

    lc_messages = []
    for msg in history:
        if msg.role == "user":
            lc_messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            lc_messages.append(AIMessage(content=msg.content))

    lc_messages.append(HumanMessage(content=message))

    initial_state = {
        "messages": lc_messages,
        "current_agent": None,
        "task_type": None,
        "intermediate_results": {},
        "user_context": business_context,
        "session_id": session_id,
        "agent_thoughts": []
    }

    graph = get_graph()
    full_content = ""
    agent_used = "general"
    thoughts = []

    try:
        async for event in graph.astream_events(initial_state, version="v2"):
            kind = event.get("event", "")
            name = event.get("name", "")

            if kind == "on_chain_end" and name == "orchestrator":
                data = event.get("data", {})
                output = data.get("output", {})
                agent_used = output.get("current_agent", "general")
                new_thoughts = output.get("agent_thoughts", [])
                for t in new_thoughts:
                    if t not in thoughts:
                        thoughts.append(t)
                        yield f"data: {json.dumps({'type': 'thought', 'content': t, 'agent': agent_used})}\n\n"
                yield f"data: {json.dumps({'type': 'agent', 'agent': agent_used})}\n\n"

            elif kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    if not (hasattr(chunk, "tool_call_chunks") and chunk.tool_call_chunks):
                        token = chunk.content
                        full_content += token
                        yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    if full_content:
        await cache_set(cache_key, {
            "agent": agent_used,
            "thoughts": thoughts,
            "content": full_content
        }, ttl=1800)

    human_msg = Message(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="user",
        content=message,
        agent=None
    )
    ai_msg = Message(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="assistant",
        content=full_content,
        agent=agent_used
    )
    db.add(human_msg)
    db.add(ai_msg)
    await db.commit()

    yield f"data: {json.dumps({'type': 'done', 'agent': agent_used})}\n\n"


@router.post("/stream")
async def chat_stream(body: ChatRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).where(Session.id == body.session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    history_result = await db.execute(
        select(Message)
        .where(Message.session_id == body.session_id)
        .order_by(Message.created_at)
    )
    history = history_result.scalars().all()

    return StreamingResponse(
        stream_agent_response(
            message=body.message,
            session_id=body.session_id,
            history=history,
            business_context=session.business_context,
            db=db
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )
