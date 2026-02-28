from __future__ import annotations

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Index, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, new_uuid
from app.models.enums import RoleType


class User(Base, TimestampMixin):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    display_name: Mapped[str | None] = mapped_column(
        String(128), nullable=True)
    locale: Mapped[str | None] = mapped_column(String(16), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True)

    chat_threads = relationship("ChatThread", back_populates="user")
    chat_messages = relationship("ChatMessage", back_populates="user")
    safety_events = relationship("SafetyEvent", back_populates="user")
    profiles = relationship("UserProfile", back_populates="user")
    preferences = relationship("UserPreference", back_populates="user")
    memory_entries = relationship("MemoryEntry", back_populates="user")
    recommendation_requests = relationship(
        "RecommendationRequest", back_populates="user")
    provider_events = relationship("ProviderEvent", back_populates="user")
    audit_events = relationship("AuditEvent", back_populates="user")
    voice_events = relationship("VoiceEvent", back_populates="user")
    family_share_consents = relationship(
        "FamilyShareConsent", back_populates="user")
    family_share_cards = relationship("FamilyShareCard", back_populates="user")


class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", "profile_key",
                         name="uq_user_profiles_user_id_key"),
        Index("ix_user_profiles_user_id", "user_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    profile_key: Mapped[str] = mapped_column(String(128), nullable=False)
    profile_value: Mapped[str] = mapped_column(Text, nullable=False)
    is_sensitive: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False)
    source: Mapped[str] = mapped_column(
        String(64), nullable=False, default="explicit")
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    user = relationship("User", back_populates="profiles")


class UserPreference(Base, TimestampMixin):
    __tablename__ = "user_preferences"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "role",
            "preference_tag",
            name="uq_user_preferences_user_role_tag",
        ),
        Index("ix_user_preferences_user_id_role", "user_id", "role"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[RoleType | None] = mapped_column(
        Enum(RoleType, name="role_type"),
        nullable=True,
    )
    preference_tag: Mapped[str] = mapped_column(String(128), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    user = relationship("User", back_populates="preferences")
