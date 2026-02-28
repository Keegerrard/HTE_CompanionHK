from __future__ import annotations

from sqlalchemy import Enum, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, new_uuid
from app.models.enums import AuditEventType, ProviderEventScope, ProviderEventStatus, RoleType


class ProviderEvent(Base, TimestampMixin):
    __tablename__ = "provider_events"
    __table_args__ = (
        Index("ix_provider_events_request_id", "request_id"),
        Index("ix_provider_events_user_created", "user_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str | None] = mapped_column(
        String(128),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    role: Mapped[RoleType | None] = mapped_column(
        Enum(RoleType, name="role_type"),
        nullable=True,
    )
    scope: Mapped[ProviderEventScope] = mapped_column(
        Enum(ProviderEventScope, name="provider_event_scope"),
        nullable=False,
    )
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    runtime: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[ProviderEventStatus] = mapped_column(
        Enum(ProviderEventStatus, name="provider_event_status"),
        nullable=False,
    )
    fallback_reason: Mapped[str | None] = mapped_column(
        String(128), nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSON, nullable=False, default=dict)

    user = relationship("User", back_populates="provider_events")


class AuditEvent(Base, TimestampMixin):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_event_type_created", "event_type", "created_at"),
        Index("ix_audit_events_user_created", "user_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str | None] = mapped_column(
        String(128),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    role: Mapped[RoleType | None] = mapped_column(
        Enum(RoleType, name="role_type"),
        nullable=True,
    )
    thread_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    event_type: Mapped[AuditEventType] = mapped_column(
        Enum(AuditEventType, name="audit_event_type"),
        nullable=False,
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSON, nullable=False, default=dict)

    user = relationship("User", back_populates="audit_events")
