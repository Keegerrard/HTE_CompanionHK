from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.chat import ChatMessage, ChatThread, SafetyEvent
from app.models.enums import RoleType, SafetyRiskLevel


class ChatRepository:
    def __init__(self, session: Session):
        self._session = session

    def get_or_create_thread(self, *, user_id: str, role: RoleType, thread_id: str) -> ChatThread:
        stmt = select(ChatThread).where(
            ChatThread.user_id == user_id,
            ChatThread.role == role,
            ChatThread.thread_id == thread_id,
        )
        thread = self._session.scalar(stmt)
        if thread is None:
            thread = ChatThread(user_id=user_id, role=role,
                                thread_id=thread_id)
            self._session.add(thread)
            self._session.flush()
        return thread

    def create_chat_message(
        self,
        *,
        thread_pk: str,
        user_id: str,
        role: RoleType,
        thread_id: str,
        request_id: str,
        user_message: str,
        assistant_reply: str,
        runtime: str,
        provider: str,
        provider_fallback_reason: str,
        context_snapshot: dict[str, object] | None,
    ) -> ChatMessage:
        message = ChatMessage(
            thread_pk=thread_pk,
            user_id=user_id,
            role=role,
            thread_id=thread_id,
            request_id=request_id,
            user_message=user_message,
            assistant_reply=assistant_reply,
            runtime=runtime,
            provider=provider,
            provider_fallback_reason=provider_fallback_reason,
            context_snapshot=context_snapshot,
        )
        self._session.add(message)
        self._session.flush()
        return message

    def create_safety_event(
        self,
        *,
        chat_message_id: str,
        thread_pk: str,
        user_id: str,
        role: RoleType,
        thread_id: str,
        request_id: str,
        risk_level: SafetyRiskLevel,
        show_crisis_banner: bool,
        emotion_label: str | None = None,
        emotion_score: float | None = None,
    ) -> SafetyEvent:
        safety_event = SafetyEvent(
            chat_message_id=chat_message_id,
            thread_pk=thread_pk,
            user_id=user_id,
            role=role,
            thread_id=thread_id,
            request_id=request_id,
            risk_level=risk_level,
            show_crisis_banner=show_crisis_banner,
            emotion_label=emotion_label,
            emotion_score=emotion_score,
        )
        self._session.add(safety_event)
        self._session.flush()
        return safety_event

    def list_recent_messages(
        self,
        *,
        user_id: str,
        role: RoleType,
        thread_id: str,
        limit: int,
    ) -> list[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(
                ChatMessage.user_id == user_id,
                ChatMessage.role == role,
                ChatMessage.thread_id == thread_id,
            )
            .order_by(desc(ChatMessage.created_at))
            .limit(limit)
        )
        return list(self._session.scalars(stmt))
