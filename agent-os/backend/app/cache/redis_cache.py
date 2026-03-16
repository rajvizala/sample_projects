import json
import hashlib
import redis.asyncio as aioredis
from typing import Any, Optional
from ..config import get_settings

settings = get_settings()

_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
            await _redis_client.ping()
        except Exception:
            _redis_client = None
    return _redis_client


def make_cache_key(prefix: str, data: Any) -> str:
    serialized = json.dumps(data, sort_keys=True)
    hash_val = hashlib.sha256(serialized.encode()).hexdigest()[:16]
    return f"agentOS:{prefix}:{hash_val}"


async def cache_get(key: str) -> Optional[dict]:
    client = await get_redis()
    if client is None:
        return None
    try:
        value = await client.get(key)
        return json.loads(value) if value else None
    except Exception:
        return None


async def cache_set(key: str, value: dict, ttl: int = None) -> bool:
    client = await get_redis()
    if client is None:
        return False
    try:
        ttl = ttl or settings.redis_ttl
        await client.setex(key, ttl, json.dumps(value))
        return True
    except Exception:
        return False


async def cache_delete(key: str) -> bool:
    client = await get_redis()
    if client is None:
        return False
    try:
        await client.delete(key)
        return True
    except Exception:
        return False
