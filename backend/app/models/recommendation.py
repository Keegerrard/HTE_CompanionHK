from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, Enum, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, new_uuid
from app.models.enums import RoleType, TravelMode


class RecommendationRequest(Base, TimestampMixin):
    __tablename__ = "recommendation_requests"
    __table_args__ = (
        Index("ix_recommendation_requests_user_role_created",
              "user_id", "role", "created_at"),
        Index("ix_recommendation_requests_request_id", "request_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=new_uuid)
    request_id: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True)
    user_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[RoleType] = mapped_column(
        Enum(RoleType, name="role_type"),
        nullable=False,
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    max_results: Mapped[int] = mapped_column(Integer, nullable=False)
    preference_tags: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list)
    travel_mode: Mapped[TravelMode] = mapped_column(
        Enum(TravelMode, name="travel_mode"),
        nullable=False,
    )
    user_location_geohash: Mapped[str | None] = mapped_column(
        String(16), nullable=True)
    user_location_region: Mapped[str | None] = mapped_column(
        String(128), nullable=True)
    weather_condition: Mapped[str | None] = mapped_column(
        String(32), nullable=True)
    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    degraded: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False)
    fallback_reason: Mapped[str | None] = mapped_column(
        String(128), nullable=True)

    user = relationship("User", back_populates="recommendation_requests")
    items = relationship("RecommendationItem",
                         back_populates="recommendation_request")


class RecommendationItem(Base, TimestampMixin):
    __tablename__ = "recommendation_items"
    __table_args__ = (
        CheckConstraint("fit_score >= 0.0 AND fit_score <= 1.0",
                        name="ck_recommendation_items_fit_score_range"),
        Index("ix_recommendation_items_request_id",
              "recommendation_request_id"),
        Index("ix_recommendation_items_place_id", "place_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=new_uuid)
    recommendation_request_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("recommendation_requests.id", ondelete="CASCADE"),
        nullable=False,
    )
    place_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    user_ratings_total: Mapped[int | None] = mapped_column(
        Integer, nullable=True)
    types: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list)
    place_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    place_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    maps_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    distance_text: Mapped[str | None] = mapped_column(
        String(32), nullable=True)
    duration_text: Mapped[str | None] = mapped_column(
        String(32), nullable=True)
    fit_score: Mapped[float] = mapped_column(Float, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)

    recommendation_request = relationship(
        "RecommendationRequest", back_populates="items")
