import hashlib
import math
from typing import Protocol


class EmbeddingProvider(Protocol):
    def embed(self, text: str) -> list[float]:
        ...


class DeterministicEmbeddingProvider:
    """
    Lightweight deterministic embedding for local/dev usage.

    This keeps SQL/vector paths fully functional and provides a clean
    extension point for replacing with a real model-backed provider later.
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

        norm = math.sqrt(sum(component * component for component in values))
        if norm <= 0:
            return values
        return [component / norm for component in values]
