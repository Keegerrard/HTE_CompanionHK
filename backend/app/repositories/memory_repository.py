from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.enums import MemoryEntryType, RoleType
from app.models.memory import MemoryEmbedding, MemoryEntry


class MemoryRepository:
    def __init__(self, session: Session):
        self._session = session

    def list_profile_memory(self, *, user_id: str, role: RoleType, limit: int) -> list[MemoryEntry]:
        stmt = (
            select(MemoryEntry)
            .where(
                MemoryEntry.user_id == user_id,
                (MemoryEntry.role == role) | (MemoryEntry.role.is_(None)),
                MemoryEntry.entry_type.in_(
                    [MemoryEntryType.profile_fact, MemoryEntryType.preference]
                ),
            )
            .order_by(desc(MemoryEntry.created_at))
            .limit(limit)
        )
        return list(self._session.scalars(stmt))

    def list_retrieval_memory(
        self,
        *,
        user_id: str,
        role: RoleType,
        top_k: int,
        query_embedding: list[float] | None = None,
    ) -> list[MemoryEntry]:
        stmt = (
            select(MemoryEntry)
            .join(MemoryEmbedding, MemoryEmbedding.memory_entry_id == MemoryEntry.id)
            .where(
                MemoryEntry.user_id == user_id,
                (MemoryEntry.role == role) | (MemoryEntry.role.is_(None)),
            )
        )
        if query_embedding:
            stmt = stmt.order_by(
                MemoryEmbedding.embedding.cosine_distance(query_embedding),
                desc(MemoryEmbedding.created_at),
            )
        else:
            stmt = stmt.order_by(desc(MemoryEmbedding.created_at))
        stmt = stmt.limit(top_k)
        return list(self._session.scalars(stmt))

    def create_memory_entry(
        self,
        *,
        user_id: str,
        role: RoleType | None,
        thread_id: str | None,
        entry_type: MemoryEntryType,
        content: str,
        write_reason: str,
        source_provider: str | None,
        created_by_request_id: str | None,
        metadata_json: dict[str, object] | None = None,
        is_sensitive: bool = False,
    ) -> MemoryEntry:
        memory_entry = MemoryEntry(
            user_id=user_id,
            role=role,
            thread_id=thread_id,
            entry_type=entry_type,
            content=content,
            write_reason=write_reason,
            source_provider=source_provider,
            created_by_request_id=created_by_request_id,
            metadata_json=metadata_json or {},
            is_sensitive=is_sensitive,
        )
        self._session.add(memory_entry)
        self._session.flush()
        return memory_entry

    def create_memory_embedding(
        self,
        *,
        memory_entry_id: str,
        user_id: str,
        role: RoleType | None,
        embedding_model: str,
        embedding_dimensions: int,
        embedding: list[float],
        distance_metric: str = "cosine",
    ) -> MemoryEmbedding:
        memory_embedding = MemoryEmbedding(
            memory_entry_id=memory_entry_id,
            user_id=user_id,
            role=role,
            embedding_model=embedding_model,
            embedding_dimensions=embedding_dimensions,
            embedding=embedding,
            distance_metric=distance_metric,
        )
        self._session.add(memory_embedding)
        self._session.flush()
        return memory_embedding
