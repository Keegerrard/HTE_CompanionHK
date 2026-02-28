from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Enum, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, new_uuid
from app.models.enums import MemoryEntryType, RoleType


class MemoryEntry(Base, TimestampMixin):
    __tablename__ = "memory_entries"
    __table_args__ = (
        Index("ix_memory_entries_user_role_type_created",
              "user_id", "role", "entry_type", "created_at"),
        Index("ix_memory_entries_thread_id", "thread_id"),
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
    thread_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    entry_type: Mapped[MemoryEntryType] = mapped_column(
        Enum(MemoryEntryType, name="memory_entry_type"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_sensitive: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False)
    write_reason: Mapped[str] = mapped_column(String(128), nullable=False)
    source_provider: Mapped[str | None] = mapped_column(
        String(64), nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSON, nullable=False, default=dict)
    created_by_request_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True)

    user = relationship("User", back_populates="memory_entries")
    embeddings = relationship("MemoryEmbedding", back_populates="memory_entry")


class MemoryEmbedding(Base, TimestampMixin):
    __tablename__ = "memory_embeddings"
    __table_args__ = (
        UniqueConstraint("memory_entry_id", "embedding_model",
                         name="uq_memory_embeddings_entry_model"),
        Index("ix_memory_embeddings_user_role", "user_id", "role"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=new_uuid)
    memory_entry_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("memory_entries.id", ondelete="CASCADE"),
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
    embedding_model: Mapped[str] = mapped_column(String(128), nullable=False)
    embedding_dimensions: Mapped[int] = mapped_column(Integer, nullable=False)
    distance_metric: Mapped[str] = mapped_column(
        String(24), nullable=False, default="cosine")
    embedding: Mapped[list[float]] = mapped_column(Vector(), nullable=False)

    memory_entry = relationship("MemoryEntry", back_populates="embeddings")
