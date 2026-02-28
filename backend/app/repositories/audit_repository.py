from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.audit import AuditEvent, ProviderEvent
from app.models.enums import (
    AuditEventType,
    ProviderEventScope,
    ProviderEventStatus,
    RoleType,
)


class AuditRepository:
    def __init__(self, session: Session):
        self._session = session

    def create_provider_event(
        self,
        *,
        user_id: str | None,
        request_id: str | None,
        role: RoleType | None,
        scope: ProviderEventScope,
        provider_name: str,
        runtime: str | None,
        status: ProviderEventStatus,
        fallback_reason: str | None = None,
        metadata_json: dict[str, object] | None = None,
    ) -> ProviderEvent:
        provider_event = ProviderEvent(
            user_id=user_id,
            request_id=request_id,
            role=role,
            scope=scope,
            provider_name=provider_name,
            runtime=runtime,
            status=status,
            fallback_reason=fallback_reason,
            metadata_json=metadata_json or {},
        )
        self._session.add(provider_event)
        self._session.flush()
        return provider_event

    def create_audit_event(
        self,
        *,
        event_type: AuditEventType,
        user_id: str | None,
        request_id: str | None = None,
        role: RoleType | None = None,
        thread_id: str | None = None,
        message: str | None = None,
        metadata_json: dict[str, object] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            request_id=request_id,
            role=role,
            thread_id=thread_id,
            message=message,
            metadata_json=metadata_json or {},
        )
        self._session.add(event)
        self._session.flush()
        return event
