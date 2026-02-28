from app.core.settings import Settings
from app.runtime.factory import build_runtime


def test_runtime_factory_uses_simple_by_default() -> None:
    settings = Settings(FEATURE_LANGGRAPH_ENABLED=False)

    runtime = build_runtime(settings)

    assert runtime.runtime_name == "simple"


def test_runtime_factory_uses_langgraph_when_flag_enabled() -> None:
    settings = Settings(
        FEATURE_LANGGRAPH_ENABLED=True,
        LANGGRAPH_CHECKPOINTER_BACKEND="postgres"
    )

    runtime = build_runtime(settings)

    assert runtime.runtime_name == "langgraph"
    assert getattr(runtime, "checkpointer_backend") == "memory"
