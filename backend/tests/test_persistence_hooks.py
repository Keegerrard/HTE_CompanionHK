from types import SimpleNamespace

from app.core.settings import Settings
from app.models.enums import AuditEventType, MemoryEntryType, RoleType
from app.schemas.chat import SafetyResult
from app.schemas.recommendations import (
    Coordinates,
    RecommendationContext,
    RecommendationItem,
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.chat_orchestrator import ChatOrchestrator
from app.services.recommendation_service import RecommendationService


class _SessionContext:
    def __init__(self, session: object):
        self._session = session

    def __enter__(self) -> object:
        return self._session

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class _FakeSession:
    def __init__(self) -> None:
        self.committed = False

    def commit(self) -> None:
        self.committed = True


def test_chat_persistence_writes_audited_memory_entry(monkeypatch) -> None:
    import app.services.chat_orchestrator as chat_module

    fake_session = _FakeSession()
    captured: dict[str, object] = {"audit_event_types": []}

    monkeypatch.setattr(chat_module, "SessionLocal",
                        lambda: _SessionContext(fake_session))

    class FakeUserRepository:
        def __init__(self, session: object):
            _ = session

        def ensure_user(self, user_id: str) -> None:
            captured["user_id"] = user_id

    class FakeChatRepository:
        def __init__(self, session: object):
            _ = session

        def get_or_create_thread(self, **kwargs) -> SimpleNamespace:
            captured["thread_kwargs"] = kwargs
            return SimpleNamespace(id="thread-pk")

        def create_chat_message(self, **kwargs) -> SimpleNamespace:
            captured["message_kwargs"] = kwargs
            return SimpleNamespace(id="chat-message-pk")

        def create_safety_event(self, **kwargs) -> None:
            captured["safety_kwargs"] = kwargs

    class FakeMemoryRepository:
        def __init__(self, session: object):
            _ = session

        def create_memory_entry(self, **kwargs) -> SimpleNamespace:
            captured["memory_kwargs"] = kwargs
            return SimpleNamespace(id="memory-entry-pk", entry_type=MemoryEntryType.summary)

        def create_memory_embedding(self, **kwargs) -> SimpleNamespace:
            captured["embedding_kwargs"] = kwargs
            return SimpleNamespace(id="memory-embedding-pk")

    class FakeAuditRepository:
        def __init__(self, session: object):
            _ = session

        def create_provider_event(self, **kwargs) -> None:
            captured["provider_event_kwargs"] = kwargs

        def create_audit_event(self, **kwargs) -> None:
            captured["audit_event_types"].append(kwargs["event_type"])

    monkeypatch.setattr(chat_module, "UserRepository", FakeUserRepository)
    monkeypatch.setattr(chat_module, "ChatRepository", FakeChatRepository)
    monkeypatch.setattr(chat_module, "MemoryRepository", FakeMemoryRepository)
    monkeypatch.setattr(chat_module, "AuditRepository", FakeAuditRepository)

    orchestrator = ChatOrchestrator()
    orchestrator._persist_chat_turn(
        request_id="chat-request-1",
        user_id="chat-user",
        role="companion",
        thread_id="chat-user-companion-thread",
        user_message="I had a rough day.",
        assistant_reply="I am here with you.",
        runtime="simple",
        provider_route="mock",
        provider_fallback_reason="not_applicable",
        context_snapshot={"memory": {}},
        safety=SafetyResult(risk_level="low", show_crisis_banner=False),
    )

    assert fake_session.committed is True
    assert captured["memory_kwargs"]["write_reason"] == "chat_turn_summary"
    assert captured["memory_kwargs"]["entry_type"] == MemoryEntryType.summary
    assert captured["embedding_kwargs"]["embedding_model"] == "text-embedding-3-small"
    assert len(captured["embedding_kwargs"]["embedding"]) > 0
    assert AuditEventType.memory_write in captured["audit_event_types"]


def test_recommendation_persistence_redacts_user_location(monkeypatch) -> None:
    import app.services.recommendation_service as recommendation_module

    fake_session = _FakeSession()
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        recommendation_module,
        "SessionLocal",
        lambda: _SessionContext(fake_session),
    )

    class FakeUserRepository:
        def __init__(self, session: object):
            _ = session

        def ensure_user(self, user_id: str) -> None:
            captured["user_id"] = user_id

    class FakeRecommendationRepository:
        def __init__(self, session: object):
            _ = session

        def create_request(self, **kwargs) -> SimpleNamespace:
            captured["request_kwargs"] = kwargs
            return SimpleNamespace(id="recommendation-request-pk")

        def create_items(self, **kwargs) -> list[object]:
            captured["items_kwargs"] = kwargs
            return []

    class FakeAuditRepository:
        def __init__(self, session: object):
            _ = session

        def create_provider_event(self, **kwargs) -> None:
            captured.setdefault("provider_events", []).append(kwargs)

        def create_audit_event(self, **kwargs) -> None:
            captured["audit_kwargs"] = kwargs

    monkeypatch.setattr(recommendation_module,
                        "UserRepository", FakeUserRepository)
    monkeypatch.setattr(
        recommendation_module,
        "RecommendationRepository",
        FakeRecommendationRepository,
    )
    monkeypatch.setattr(recommendation_module,
                        "AuditRepository", FakeAuditRepository)

    service = RecommendationService()
    monkeypatch.setattr(
        service,
        "_coarse_user_location",
        lambda **_: ("coarse_token_123", "22.28,114.16"),
    )

    request = RecommendationRequest(
        user_id="recommend-user",
        role="local_guide",
        query="quiet cafe",
        latitude=22.2819,
        longitude=114.1589,
        max_results=5,
        preference_tags=["quiet"],
        travel_mode="walking",
    )
    response = RecommendationResponse(
        request_id="recommendation-request-1",
        recommendations=[
            RecommendationItem(
                place_id="place-1",
                name="Quiet Cafe",
                address="Central, Hong Kong",
                rating=4.5,
                user_ratings_total=1200,
                types=["cafe"],
                location=Coordinates(latitude=22.283001, longitude=114.159002),
                fit_score=0.91,
                rationale="Great fit for your query.",
            )
        ],
        context=RecommendationContext(
            weather_condition="cloudy",
            temperature_c=25.1,
            degraded=False,
            fallback_reason=None,
        ),
    )

    service._persist_recommendation_result(
        request=request,
        response=response,
        maps_provider_name="google-maps",
        weather_provider_name="open-meteo",
    )

    assert fake_session.committed is True
    request_kwargs = captured["request_kwargs"]
    assert request_kwargs["user_location_geohash"] == "coarse_token_123"
    assert request_kwargs["user_location_region"] == "22.28,114.16"
    assert "latitude" not in request_kwargs and "longitude" not in request_kwargs

    persisted_item = captured["items_kwargs"]["recommendations"][0]
    assert persisted_item.location.latitude == 22.283001
    assert persisted_item.location.longitude == 114.159002


def test_context_builder_respects_retrieval_top_k(monkeypatch) -> None:
    import app.memory.context_builder as context_builder_module

    captured: dict[str, object] = {}
    settings = Settings(MEMORY_RETRIEVAL_TOP_K=3,
                        REDIS_URL="redis://localhost:6379/0")
    context_builder = context_builder_module.ConversationContextBuilder(
        settings)

    class FakeRedis:
        def lrange(self, *_args, **_kwargs) -> list[str]:
            return ['{"request_id":"1","user_message":"hello","assistant_reply":"hi"}']

    monkeypatch.setattr(context_builder_module,
                        "get_redis_client", lambda: FakeRedis())
    monkeypatch.setattr(
        context_builder_module,
        "SessionLocal",
        lambda: _SessionContext(object()),
    )

    class FakeUserRepository:
        def __init__(self, session: object):
            _ = session

        def list_profiles(self, _user_id: str) -> list[SimpleNamespace]:
            return []

        def list_preferences(self, *, user_id: str, role: RoleType) -> list[SimpleNamespace]:
            _ = user_id, role
            return []

    class FakeMemoryRepository:
        def __init__(self, session: object):
            _ = session

        def list_retrieval_memory(
            self,
            *,
            user_id: str,
            role: RoleType,
            top_k: int,
            query_embedding: list[float] | None = None,
        ) -> list[SimpleNamespace]:
            captured["top_k"] = top_k
            captured["query_embedding"] = query_embedding
            _ = user_id, role
            return [
                SimpleNamespace(
                    entry_type=SimpleNamespace(value="summary"),
                    content="retrieval-item",
                    source_provider="mock",
                )
            ]

    monkeypatch.setattr(context_builder_module,
                        "UserRepository", FakeUserRepository)
    monkeypatch.setattr(context_builder_module,
                        "MemoryRepository", FakeMemoryRepository)

    context = context_builder.build(
        user_id="context-user",
        thread_id="context-thread",
        role="companion",
        message="Need help planning today.",
    )

    assert captured["top_k"] == 3
    assert isinstance(captured["query_embedding"], list)
    assert len(captured["query_embedding"]
               ) == settings.memory_embedding_dimensions
    assert context["memory"]["long_term_retrieval"]["top_k"] == 3
    assert len(context["memory"]["long_term_retrieval"]["entries"]) == 1
