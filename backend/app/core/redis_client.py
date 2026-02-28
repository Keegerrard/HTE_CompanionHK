import json
from functools import lru_cache
from typing import Any

from redis import Redis

from app.schemas.chat import ChatRole
from app.core.settings import settings


def build_short_term_memory_key(*, user_id: str, role: ChatRole, thread_id: str) -> str:
    return f"memory:short_term:{user_id}:{role}:{thread_id}"


@lru_cache(maxsize=1)
def get_redis_client(redis_url: str | None = None) -> Redis:
    resolved_url = redis_url or settings.effective_redis_url
    return Redis.from_url(
        resolved_url,
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=1,
    )


def serialize_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True)


def deserialize_json(value: str | None) -> Any:
    if not value:
        return None
    return json.loads(value)
