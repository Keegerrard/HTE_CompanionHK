from typing import Any

from app.core.database import SessionLocal
from app.core.redis_client import (
    build_short_term_memory_key,
    deserialize_json,
    get_redis_client,
)
from app.core.settings import Settings
from app.memory.embeddings import DeterministicEmbeddingProvider
from app.models.enums import RoleType
from app.repositories.memory_repository import MemoryRepository
from app.repositories.user_repository import UserRepository
from app.schemas.chat import ChatRole


class ConversationContextBuilder:
    """
    Foundation memory context builder.

    This defines a single context shape that future memory adapters
    (Redis, Postgres profile memory, pgvector retrieval) can populate.
    """

    def __init__(self, settings: Settings):
        self._settings = settings
        self._embedding_provider = DeterministicEmbeddingProvider(
            settings.memory_embedding_dimensions
        )

    def build(
        self,
        *,
        user_id: str,
        thread_id: str,
        role: ChatRole,
        message: str
    ) -> dict[str, Any]:
        short_term_context: dict[str, Any] = {
            "source": "redis",
            "status": "ok",
            "entries": [],
        }
        redis_key = build_short_term_memory_key(
            user_id=user_id,
            role=role,
            thread_id=thread_id,
        )
        try:
            redis_client = get_redis_client()
            short_term_entries = redis_client.lrange(
                redis_key,
                0,
                self._settings.memory_short_term_max_turns - 1,
            )
            short_term_context["entries"] = [
                entry
                for entry in (
                    deserialize_json(raw_value)
                    for raw_value in short_term_entries
                )
                if isinstance(entry, dict)
            ]
            short_term_context["count"] = len(short_term_context["entries"])
        except Exception:
            short_term_context["status"] = "degraded"
            short_term_context["fallback_reason"] = "redis_unavailable"

        long_term_profile: dict[str, Any] = {
            "source": "postgres",
            "status": "ok",
            "profiles": [],
            "preferences": [],
        }
        long_term_retrieval: dict[str, Any] = {
            "source": "pgvector",
            "status": "ok",
            "top_k": self._settings.memory_retrieval_top_k,
            "entries": [],
        }

        try:
            role_enum = RoleType(role)
            with SessionLocal() as session:
                user_repository = UserRepository(session)
                memory_repository = MemoryRepository(session)

                profiles = user_repository.list_profiles(user_id)
                preferences = user_repository.list_preferences(
                    user_id=user_id,
                    role=role_enum,
                )
                retrieval_entries = memory_repository.list_retrieval_memory(
                    user_id=user_id,
                    role=role_enum,
                    top_k=self._settings.memory_retrieval_top_k,
                    query_embedding=self._embedding_provider.embed(message),
                )

                long_term_profile["profiles"] = [
                    {
                        "key": profile.profile_key,
                        "value": profile.profile_value,
                        "source": profile.source,
                        "is_sensitive": profile.is_sensitive,
                    }
                    for profile in profiles
                ]
                long_term_profile["preferences"] = [
                    {
                        "tag": preference.preference_tag,
                        "weight": preference.weight,
                        "role": None if preference.role is None else preference.role.value,
                    }
                    for preference in preferences
                ]
                long_term_retrieval["entries"] = [
                    {
                        "entry_type": entry.entry_type.value,
                        "content": entry.content,
                        "source_provider": entry.source_provider,
                    }
                    for entry in retrieval_entries
                ]
        except Exception:
            long_term_profile["status"] = "degraded"
            long_term_profile["fallback_reason"] = "postgres_unavailable"
            long_term_retrieval["status"] = "degraded"
            long_term_retrieval["fallback_reason"] = "pgvector_unavailable"

        return {
            "user_id": user_id,
            "thread_id": thread_id,
            "role": role,
            "input_preview": message[:180],
            "memory": {
                "strategy": self._settings.memory_long_term_strategy,
                "short_term": short_term_context,
                "long_term_profile": long_term_profile,
                "long_term_retrieval": long_term_retrieval,
            }
        }
