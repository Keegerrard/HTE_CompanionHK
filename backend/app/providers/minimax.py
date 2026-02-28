import logging
from typing import Any

from pydantic import SecretStr

from app.providers.base import ChatProvider

logger = logging.getLogger(__name__)

try:
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI

    LANGCHAIN_AVAILABLE = True
except ImportError:
    AIMessage = HumanMessage = SystemMessage = None  # type: ignore[assignment]
    ChatOpenAI = None  # type: ignore[assignment]
    LANGCHAIN_AVAILABLE = False

class MiniMaxChatProvider(ChatProvider):
    """
    MiniMax provider using LangChain's ChatOpenAI pointed at MiniMax's
    OpenAI-compatible endpoint (https://api.minimax.io/v1).

    When the LangGraph runtime is active, context may contain pre-built
    'langchain_messages'. If present, we use them directly. Otherwise we
    build messages from the raw context (system_prompt + plain message).
    """

    provider_name = "minimax"

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "MiniMax-M2.5",
        base_url: str = "https://api.minimax.io/v1",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._llm: Any = None

    def _get_llm(self) -> Any:
        if self._llm is not None:
            return self._llm

        if not LANGCHAIN_AVAILABLE:
            raise RuntimeError(
                "langchain-openai is not installed. "
                "Run: pip install langchain-openai"
            )
        assert ChatOpenAI is not None

        self._llm = ChatOpenAI(
            api_key=SecretStr(self._api_key),
            base_url=self._base_url,
            model=self._model,
            temperature=self._temperature,
            model_kwargs={"max_tokens": self._max_tokens},
        )
        return self._llm

    def generate_reply(self, message: str, context: dict[str, Any] | None = None) -> str:
        ctx = context or {}
        if not LANGCHAIN_AVAILABLE:
            logger.warning("minimax_langchain_unavailable")
            return (
                "I'm having trouble connecting right now. "
                "Let me try again in a moment."
            )
        assert SystemMessage is not None
        assert HumanMessage is not None
        assert AIMessage is not None

        lc_messages = ctx.get("langchain_messages")
        if isinstance(lc_messages, list) and lc_messages:
            return self._invoke_with_messages(lc_messages)

        system_prompt = ctx.get("system_prompt", "")
        messages: list[Any] = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))

        history = ctx.get("history", [])
        if isinstance(history, list):
            for turn in history:
                if not isinstance(turn, dict):
                    continue
                role = turn.get("role", "")
                content = turn.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))

        messages.append(HumanMessage(content=message))
        return self._invoke_with_messages(messages)

    def _invoke_with_messages(self, messages: list[Any]) -> str:
        try:
            llm = self._get_llm()
            response = llm.invoke(messages)
            content = getattr(response, "content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                text_chunks = [
                    item["text"]
                    for item in content
                    if isinstance(item, dict) and isinstance(item.get("text"), str)
                ]
                if text_chunks:
                    return "\n".join(text_chunks)
            return str(content)
        except Exception:
            logger.exception("minimax_provider_error")
            return (
                "I'm having trouble connecting right now. "
                "Let me try again in a moment."
            )
