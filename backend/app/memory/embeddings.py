import hashlib
import logging
import math
from typing import Protocol

logger = logging.getLogger(__name__)


class EmbeddingProvider(Protocol):
    def embed(self, text: str) -> list[float]:
        ...


class DeterministicEmbeddingProvider:
    """
    Hash-based embedding for local dev when no API key is available.
    Not semantically meaningful -- use LangChainEmbeddingProvider in production.
    """

    def __init__(self, dimensions: int):
        self._dimensions = max(8, dimensions)

    def embed(self, text: str) -> list[float]:
        values = [0.0] * self._dimensions
        normalized_text = text.strip().lower()
        if not normalized_text:
            return values

        for token in normalized_text.split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for byte_index in range(0, len(digest), 2):
                bucket = int.from_bytes(
                    digest[byte_index:byte_index + 2], "big") % self._dimensions
                sign = 1.0 if digest[byte_index] % 2 == 0 else -1.0
                values[bucket] += sign

        norm = math.sqrt(sum(c * c for c in values))
        if norm <= 0:
            return values
        return [c / norm for c in values]


class LangChainEmbeddingProvider:
    """
    Real semantic embeddings via LangChain's OpenAI embeddings.
    Points at MiniMax's OpenAI-compatible endpoint by default,
    so it uses your MiniMax credits for embeddings too.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "text-embedding-3-small",
        base_url: str = "https://api.minimax.io/v1",
        dimensions: int = 1536,
    ):
        from langchain_openai import OpenAIEmbeddings

        self._embeddings = OpenAIEmbeddings(
            api_key=api_key,
            base_url=base_url,
            model=model,
            dimensions=dimensions,
        )
        self._dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        try:
            result = self._embeddings.embed_query(text)
            return result
        except Exception:
            logger.exception("langchain_embedding_failed, falling_back_to_deterministic")
            fallback = DeterministicEmbeddingProvider(self._dimensions)
            return fallback.embed(text)


def build_embedding_provider(
    *,
    api_key: str,
    model: str,
    base_url: str,
    dimensions: int,
) -> EmbeddingProvider:
    if api_key:
        try:
            return LangChainEmbeddingProvider(
                api_key=api_key,
                model=model,
                base_url=base_url,
                dimensions=dimensions,
            )
        except Exception:
            logger.exception("langchain_embedding_init_failed, using_deterministic")
    return DeterministicEmbeddingProvider(dimensions)
