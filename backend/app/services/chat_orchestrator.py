import logging
from datetime import datetime, timezone
from typing import cast
from uuid import uuid4

from app.core.database import SessionLocal
from app.core.redis_client import (
    build_short_term_memory_key,
    get_redis_client,
    serialize_json,
)
from app.core.settings import settings
from app.memory.embeddings import DeterministicEmbeddingProvider
from app.memory.context_builder import ConversationContextBuilder
from app.models.enums import (
    AuditEventType,
    MemoryEntryType,
    ProviderEventScope,
    ProviderEventStatus,
    RoleType,
    SafetyRiskLevel,
)
from app.providers.router import ProviderRouter
from app.repositories.audit_repository import AuditRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.memory_repository import MemoryRepository
from app.repositories.user_repository import UserRepository
from app.runtime.base import ConversationRuntime
from app.runtime.factory import build_runtime
from app.schemas.chat import ChatRequest, ChatResponse, ChatRole, SafetyResult

logger = logging.getLogger(__name__)


class ChatOrchestrator:
    """Mock orchestrator boundary for provider routing and safety hooks."""

    def __init__(
        self,
        provider_router: ProviderRouter | None = None,
        runtime: ConversationRuntime | None = None,
        context_builder: ConversationContextBuilder | None = None
    ):
        self._settings = settings
        self._provider_router = provider_router or ProviderRouter(settings)
        self._runtime = runtime or build_runtime(settings)
        self._embedding_provider = DeterministicEmbeddingProvider(
            settings.memory_embedding_dimensions
        )
        self._context_builder = context_builder or ConversationContextBuilder(
            settings)

    def _persist_short_term_memory(
        self,
        *,
        user_id: str,
        role: str,
        thread_id: str,
        request_id: str,
        user_message: str,
        assistant_reply: str,
    ) -> None:
        redis_client = get_redis_client()
        redis_key = build_short_term_memory_key(
            user_id=user_id,
            role=cast(ChatRole, role),
            thread_id=thread_id,
        )
        payload = {
            "request_id": request_id,
            "user_message": user_message,
            "assistant_reply": assistant_reply,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        pipeline = redis_client.pipeline()
        pipeline.lpush(redis_key, serialize_json(payload))
        pipeline.ltrim(
            redis_key, 0, self._settings.memory_short_term_max_turns - 1)
        pipeline.expire(
            redis_key, self._settings.memory_short_term_ttl_seconds)
        pipeline.execute()

    def _persist_chat_turn(
        self,
        *,
        request_id: str,
        user_id: str,
        role: str,
        thread_id: str,
        user_message: str,
        assistant_reply: str,
        runtime: str,
        provider_route: str,
        provider_fallback_reason: str,
        context_snapshot: dict[str, object],
        safety: SafetyResult,
    ) -> None:
        role_enum = RoleType(role)
        provider_status = (
            ProviderEventStatus.success
            if provider_fallback_reason == "not_applicable"
            else ProviderEventStatus.fallback
        )
        with SessionLocal() as session:
            user_repository = UserRepository(session)
            chat_repository = ChatRepository(session)
            memory_repository = MemoryRepository(session)
            audit_repository = AuditRepository(session)

            user_repository.ensure_user(user_id)
            thread = chat_repository.get_or_create_thread(
                user_id=user_id,
                role=role_enum,
                thread_id=thread_id,
            )

            message = chat_repository.create_chat_message(
                thread_pk=thread.id,
                user_id=user_id,
                role=role_enum,
                thread_id=thread_id,
                request_id=request_id,
                user_message=user_message,
                assistant_reply=assistant_reply,
                runtime=runtime,
                provider=provider_route,
                provider_fallback_reason=provider_fallback_reason,
                context_snapshot=context_snapshot,
            )
            chat_repository.create_safety_event(
                chat_message_id=message.id,
                thread_pk=thread.id,
                user_id=user_id,
                role=role_enum,
                thread_id=thread_id,
                request_id=request_id,
                risk_level=SafetyRiskLevel(safety.risk_level),
                show_crisis_banner=safety.show_crisis_banner,
            )

            audit_repository.create_provider_event(
                user_id=user_id,
                request_id=request_id,
                role=role_enum,
                scope=ProviderEventScope.chat,
                provider_name=provider_route,
                runtime=runtime,
                status=provider_status,
                fallback_reason=provider_fallback_reason,
                metadata_json={"thread_id": thread_id},
            )
            audit_repository.create_audit_event(
                event_type=AuditEventType.safety_event,
                user_id=user_id,
                request_id=request_id,
                role=role_enum,
                thread_id=thread_id,
                metadata_json={
                    "risk_level": safety.risk_level,
                    "show_crisis_banner": safety.show_crisis_banner,
                },
            )

            summary_excerpt = user_message.strip()[:200]
            memory_entry = memory_repository.create_memory_entry(
                user_id=user_id,
                role=role_enum,
                thread_id=thread_id,
                entry_type=MemoryEntryType.summary,
                content=f"User intent summary: {summary_excerpt}",
                write_reason="chat_turn_summary",
                source_provider=provider_route,
                created_by_request_id=request_id,
                metadata_json={
                    "runtime": runtime,
                    "request_id": request_id,
                },
                is_sensitive=False,
            )
            memory_embedding = self._embedding_provider.embed(
                f"{user_message}\n{assistant_reply}"
            )
            memory_repository.create_memory_embedding(
                memory_entry_id=memory_entry.id,
                user_id=user_id,
                role=role_enum,
                embedding_model=self._settings.memory_embedding_model,
                embedding_dimensions=len(memory_embedding),
                embedding=memory_embedding,
                distance_metric="cosine",
            )
            audit_repository.create_audit_event(
                event_type=AuditEventType.memory_write,
                user_id=user_id,
                request_id=request_id,
                role=role_enum,
                thread_id=thread_id,
                metadata_json={
                    "memory_entry_id": memory_entry.id,
                    "entry_type": memory_entry.entry_type.value,
                },
            )

            session.commit()

    def generate_reply(self, chat_request: ChatRequest) -> ChatResponse:
        request_id = str(uuid4())
        role = chat_request.role
        thread_id = chat_request.thread_id or f"{chat_request.user_id}-{role}-thread"
        provider = self._provider_router.resolve_chat_provider()
        provider_route = provider.provider_name
        fallback_reason = (
            "provider_disabled_or_unavailable"
            if provider_route != settings.chat_provider and settings.chat_provider != "mock"
            else "not_applicable"
        )
        context = self._context_builder.build(
            user_id=chat_request.user_id,
            thread_id=thread_id,
            role=role,
            message=chat_request.message
        )

        logger.info(
            "chat_orchestrated request_id=%s role=%s thread_id=%s runtime=%s provider_route=%s fallback_reason=%s user_id=%s",
            request_id,
            role,
            thread_id,
            self._runtime.runtime_name,
            provider_route,
            fallback_reason,
            chat_request.user_id
        )

        reply = self._runtime.generate_reply(
            message=chat_request.message,
            provider=provider,
            context=context
        )
        safety = SafetyResult(risk_level="low", show_crisis_banner=False)

        try:
            self._persist_chat_turn(
                request_id=request_id,
                user_id=chat_request.user_id,
                role=role,
                thread_id=thread_id,
                user_message=chat_request.message,
                assistant_reply=reply,
                runtime=self._runtime.runtime_name,
                provider_route=provider_route,
                provider_fallback_reason=fallback_reason,
                context_snapshot=context,
                safety=safety,
            )
        except Exception:
            logger.exception(
                "chat_persistence_failed request_id=%s user_id=%s role=%s thread_id=%s",
                request_id,
                chat_request.user_id,
                role,
                thread_id,
            )

        try:
            self._persist_short_term_memory(
                user_id=chat_request.user_id,
                role=role,
                thread_id=thread_id,
                request_id=request_id,
                user_message=chat_request.message,
                assistant_reply=reply,
            )
        except Exception:
            logger.exception(
                "redis_short_term_memory_write_failed request_id=%s user_id=%s role=%s thread_id=%s",
                request_id,
                chat_request.user_id,
                role,
                thread_id,
            )

        return ChatResponse(
            request_id=request_id,
            thread_id=thread_id,
            runtime=self._runtime.runtime_name,
            provider=provider_route,
            reply=reply,
            safety=safety,
        )
