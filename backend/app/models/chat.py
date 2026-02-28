from __future__ import annotations

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Index, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, new_uuid
from app.models.enums import RoleType, SafetyRiskLevel


class ChatThread(Base, TimestampMixin):
    __tablename__ = "chat_threads"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "role",
            "thread_id",
            name="uq_chat_threads_user_role_thread",
        ),
        Index("ix_chat_threads_user_role_activity",
              "user_id", "role", "updated_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[RoleType] = mapped_column(
        Enum(RoleType, name="role_type"),
        nullable=False,
    )
    thread_id: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str | None] = mapped_column(String(160), nullable=True)

    user = relationship("User", back_populates="chat_threads")
    messages = relationship("ChatMessage", back_populates="thread")
    safety_events = relationship("SafetyEvent", back_populates="thread")


class ChatMessage(Base, TimestampMixin):
    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("ix_chat_messages_thread_created", "thread_id", "created_at"),
        Index("ix_chat_messages_request_id", "request_id"),
        Index("ix_chat_messages_user_role_created",
              "user_id", "role", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=new_uuid)
    thread_pk: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("chat_threads.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[RoleType] = mapped_column(
        Enum(RoleType, name="role_type"),
        nullable=False,
    )
    thread_id: Mapped[str] = mapped_column(String(128), nullable=False)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    user_message: Mapped[str] = mapped_column(Text, nullable=False)
    assistant_reply: Mapped[str] = mapped_column(Text, nullable=False)
    runtime: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_fallback_reason: Mapped[str | None] = mapped_column(
        String(128), nullable=True)
    context_snapshot: Mapped[dict[str, object] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    thread = relationship("ChatThread", back_populates="messages")
    user = relationship("User", back_populates="chat_messages")
    safety_event = relationship(
        "SafetyEvent", back_populates="chat_message", uselist=False)


class SafetyEvent(Base, TimestampMixin):
    __tablename__ = "safety_events"
    __table_args__ = (
        Index("ix_safety_events_user_risk_created",
              "user_id", "risk_level", "created_at"),
        Index("ix_safety_events_request_id", "request_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=new_uuid)
    chat_message_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("chat_messages.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    thread_pk: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("chat_threads.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[RoleType] = mapped_column(
        Enum(RoleType, name="role_type"),
        nullable=False,
    )
    thread_id: Mapped[str] = mapped_column(String(128), nullable=False)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    risk_level: Mapped[SafetyRiskLevel] = mapped_column(
        Enum(SafetyRiskLevel, name="safety_risk_level"),
        nullable=False,
    )
    show_crisis_banner: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False)
    emotion_label: Mapped[str | None] = mapped_column(
        String(64), nullable=True)
    emotion_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    chat_message = relationship("ChatMessage", back_populates="safety_event")
    thread = relationship("ChatThread", back_populates="safety_events")
    user = relationship("User", back_populates="safety_events")
