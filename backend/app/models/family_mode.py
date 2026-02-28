from __future__ import annotations

from sqlalchemy import Boolean, Enum, ForeignKey, Index, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, new_uuid
from app.models.enums import FamilyConsentScope, FamilyShareStatus, RoleType


class FamilyShareConsent(Base, TimestampMixin):
    __tablename__ = "family_share_consents"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "contact_label",
            "consent_scope",
            name="uq_family_share_consents_user_contact_scope",
        ),
        Index("ix_family_share_consents_user_active", "user_id", "is_active"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    contact_label: Mapped[str] = mapped_column(String(160), nullable=False)
    consent_scope: Mapped[FamilyConsentScope] = mapped_column(
        Enum(FamilyConsentScope, name="family_consent_scope"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True)
    granted_by_request_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True)
    revoked_by_request_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True)

    user = relationship("User", back_populates="family_share_consents")
    cards = relationship("FamilyShareCard", back_populates="consent")


class FamilyShareCard(Base, TimestampMixin):
    __tablename__ = "family_share_cards"
    __table_args__ = (
        Index("ix_family_share_cards_user_created", "user_id", "created_at"),
        Index("ix_family_share_cards_status", "share_status"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=new_uuid)
    consent_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("family_share_consents.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[RoleType | None] = mapped_column(
        Enum(RoleType, name="role_type"),
        nullable=True,
    )
    thread_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    share_status: Mapped[FamilyShareStatus] = mapped_column(
        Enum(FamilyShareStatus, name="family_share_status"),
        nullable=False,
        default=FamilyShareStatus.pending,
    )
    shared_with: Mapped[str | None] = mapped_column(String(160), nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSON, nullable=False, default=dict)

    consent = relationship("FamilyShareConsent", back_populates="cards")
    user = relationship("User", back_populates="family_share_cards")
