import json
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db, AsyncSessionLocal
from ..models import ThreatEvent
from ..background import register_callback, unregister_callback

router = APIRouter(tags=["websocket"])

_active_connections: dict[str, WebSocket] = {}


async def _broadcast_threat(event: dict):
    """Called by background monitor when a new threat is detected."""
    dead_clients = []
    for client_id, ws in list(_active_connections.items()):
        try:
            await ws.send_text(json.dumps({
                "type": "new_threat",
                "data": event
            }))
        except Exception:
            dead_clients.append(client_id)

    for cid in dead_clients:
        _active_connections.pop(cid, None)

    async with AsyncSessionLocal() as db:
        threat = ThreatEvent(
            id=event.get("id", str(uuid.uuid4())),
            threat_type=event.get("threat_type", "unknown"),
            severity=event.get("severity", "LOW"),
            risk_score=event.get("risk_score", 0.0),
            title=event.get("title", "Unknown Threat"),
            description=event.get("description", ""),
            source=event.get("source"),
            indicators=event.get("indicators", {}),
            action_required=event.get("action_required"),
        )
        db.add(threat)
        await db.commit()


register_callback(_broadcast_threat)


@router.websocket("/ws/threats")
async def threat_websocket(websocket: WebSocket):
    client_id = str(uuid.uuid4())
    await websocket.accept()
    _active_connections[client_id] = websocket

    await websocket.send_text(json.dumps({
        "type": "connected",
        "data": {
            "client_id": client_id,
            "message": "SecureSignal threat monitor connected. Watching for threats...",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }))

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        _active_connections.pop(client_id, None)
