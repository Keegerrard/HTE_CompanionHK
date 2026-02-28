import logging
from typing import Any

import httpx

from app.providers.base import RetrievalProvider

logger = logging.getLogger(__name__)

EXA_SEARCH_URL = "https://api.exa.ai/search"


class ExaRetrievalProvider(RetrievalProvider):
    """
    Exa AI retrieval provider for fresh local context
    (events, neighborhood info, trending places in Hong Kong).

    Uses the Exa REST API directly via httpx to avoid adding
    the exa-py SDK as a dependency.
    """

    provider_name = "exa"

    def __init__(self, *, api_key: str, timeout: float = 10.0):
        self._api_key = api_key
        self._timeout = timeout

    def retrieve(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        if not self._api_key:
            logger.warning("exa_api_key_missing, returning_empty")
            return []

        try:
            response = httpx.post(
                EXA_SEARCH_URL,
                headers={
                    "x-api-key": self._api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "query": f"{query} Hong Kong",
                    "type": "auto",
                    "numResults": max_results,
                    "contents": {
                        "text": {"maxCharacters": 500},
                        "highlights": {"numSentences": 2},
                    },
                },
                timeout=self._timeout,
            )
            response.raise_for_status()
            data = response.json()

            results: list[dict[str, Any]] = []
            for item in data.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "text": item.get("text", ""),
                    "highlights": item.get("highlights", []),
                    "score": item.get("score"),
                    "published_date": item.get("publishedDate"),
                })

            logger.info("exa_retrieval_success query=%s results=%d", query, len(results))
            return results

        except httpx.HTTPStatusError as exc:
            logger.error(
                "exa_api_error status=%d body=%s",
                exc.response.status_code,
                exc.response.text[:200],
            )
            return []
        except Exception:
            logger.exception("exa_retrieval_failed query=%s", query)
            return []
