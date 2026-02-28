import logging
from typing import Any, TypedDict

from app.providers.base import ChatProvider
from app.prompts.role_prompts import resolve_role_system_prompt
from app.runtime.base import ConversationRuntime

logger = logging.getLogger(__name__)
_KNOWN_ROLES = {"companion", "local_guide", "study_guide"}

try:
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.graph import END, StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:
    AIMessage = HumanMessage = SystemMessage = None  # type: ignore[assignment]
    MemorySaver = None  # type: ignore[assignment]
    StateGraph = None  # type: ignore[assignment]
    END = None  # type: ignore[assignment]
    LANGGRAPH_AVAILABLE = False


class ConversationState(TypedDict, total=False):
    history: list[dict[str, str]]
    context: dict[str, Any]
    incoming_message: str
    reply: str


class LangGraphConversationRuntime(ConversationRuntime):
    """
    LangGraph-backed runtime that manages conversation state per thread_id.

    The graph has a single 'chat' node that:
      1. Reads conversation history from checkpoint state.
      2. Builds LangChain message objects (System + History + HumanMessage).
      3. Passes them to the ChatProvider (which uses LangChain ChatOpenAI under the hood).
      4. Appends the reply to history and checkpoints automatically.

    Checkpointing means the backend remembers conversation per thread_id
    without any external DB -- LangGraph handles it via MemorySaver (in-process).
    """

    runtime_name = "langgraph"
    _SUPPORTED_CHECKPOINTER_BACKENDS = {"memory"}

    def __init__(self, checkpointer_backend: str = "memory"):
        requested_backend = (checkpointer_backend or "memory").lower()
        if requested_backend not in self._SUPPORTED_CHECKPOINTER_BACKENDS:
            logger.warning(
                "unsupported_langgraph_checkpointer_backend backend=%s, falling back to memory",
                requested_backend,
            )
            requested_backend = "memory"

        self._checkpointer_backend = requested_backend
        self._graphs: dict[str, Any] = {}
        self._checkpointer: Any = None

    @property
    def checkpointer_backend(self) -> str:
        return self._checkpointer_backend

    def _get_checkpointer(self) -> Any:
        if self._checkpointer is not None:
            return self._checkpointer
        if not LANGGRAPH_AVAILABLE or MemorySaver is None:
            raise RuntimeError(
                "langgraph is not installed. "
                "Run: pip install langgraph"
            )
        self._checkpointer = MemorySaver()
        return self._checkpointer

    def _build_langchain_messages(
        self,
        *,
        system_prompt: str,
        history: list[dict[str, str]],
        user_message: str,
    ) -> list[Any]:
        if not LANGGRAPH_AVAILABLE:
            raise RuntimeError(
                "langgraph/langchain is not installed. "
                "Run: pip install langgraph langchain-core"
            )
        assert SystemMessage is not None
        assert HumanMessage is not None
        assert AIMessage is not None
        messages: list[Any] = [SystemMessage(content=system_prompt)]
        for turn in history:
            role = turn.get("role", "")
            content = turn.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
        messages.append(HumanMessage(content=user_message))
        return messages

    def _get_or_build_graph(self, provider: ChatProvider) -> Any:
        if not LANGGRAPH_AVAILABLE or StateGraph is None or END is None:
            raise RuntimeError(
                "langgraph is not installed. "
                "Run: pip install langgraph"
            )
        provider_key = provider.provider_name
        if provider_key in self._graphs:
            return self._graphs[provider_key]

        def chat_node(state: ConversationState) -> dict[str, Any]:
            history = list(state.get("history") or [])
            incoming = state.get("incoming_message", "")
            ctx = dict(state.get("context") or {})

            system_prompt = ctx.get("system_prompt", "")
            lc_messages = self._build_langchain_messages(
                system_prompt=system_prompt,
                history=history,
                user_message=incoming,
            )

            ctx["langchain_messages"] = lc_messages
            reply = provider.generate_reply(incoming, ctx)

            history.append({"role": "user", "content": incoming})
            history.append({"role": "assistant", "content": reply})
            return {"history": history, "reply": reply}

        builder = StateGraph(ConversationState)
        builder.add_node("chat", chat_node)
        builder.set_entry_point("chat")
        builder.add_edge("chat", END)

        graph = builder.compile(checkpointer=self._get_checkpointer())
        self._graphs[provider_key] = graph
        return graph

    def generate_reply(
        self,
        *,
        message: str,
        provider: ChatProvider,
        context: dict[str, Any],
    ) -> str:
        role = context.get("role")
        if role not in _KNOWN_ROLES:
            role = "companion"

        runtime_context = dict(context)
        runtime_context["system_prompt"] = resolve_role_system_prompt(role)

        if not LANGGRAPH_AVAILABLE:
            logger.warning(
                "langgraph_runtime_requested_but_unavailable thread_id=%s",
                runtime_context.get("thread_id"),
            )
            return provider.generate_reply(message, runtime_context)

        thread_id = runtime_context.get("thread_id", "default")
        logger.info(
            "langgraph_runtime thread_id=%s role=%s provider=%s",
            thread_id,
            role,
            provider.provider_name,
        )

        graph = self._get_or_build_graph(provider)
        result = graph.invoke(
            {"incoming_message": message, "context": runtime_context},
            config={"configurable": {"thread_id": thread_id}},
        )
        if not isinstance(result, dict):
            return ""
        reply = result.get("reply", "")
        return reply if isinstance(reply, str) else str(reply)
