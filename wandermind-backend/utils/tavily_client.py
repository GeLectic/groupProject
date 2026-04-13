import asyncio
import hashlib
from typing import Any, Dict, List, Optional

from diskcache import Cache
from tavily import TavilyClient

from config import settings


class TavilySearchClient:
    def __init__(self, api_key: Optional[str] = None, cache_dir: str = ".cache/tavily") -> None:
        self.api_key = api_key or settings.tavily_api_key
        self.client = TavilyClient(api_key=self.api_key) if self.api_key else None
        self.cache = Cache(cache_dir)
        self.calls_used = 0
        self.max_calls_per_trip = settings.tavily_max_calls_per_trip
        self._lock = asyncio.Lock()

    @property
    def enabled(self) -> bool:
        return self.client is not None

    def reset_budget(self) -> None:
        self.calls_used = 0

    async def search(
        self,
        query: str,
        max_results: int = 5,
        include_raw_content: bool = False,
    ) -> List[Dict[str, Any]]:
        cache_key = self._cache_key(query, max_results, include_raw_content)
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        if not self.client:
            return []

        async with self._lock:
            if self.calls_used >= self.max_calls_per_trip:
                return []
            self.calls_used += 1

        def _do_search() -> Dict[str, Any]:
            return self.client.search(
                query=query,
                max_results=max_results,
                include_raw_content=include_raw_content,
            )

        try:
            response = await asyncio.to_thread(_do_search)
            results = response.get("results", []) if isinstance(response, dict) else []
            self.cache.set(cache_key, results, expire=60 * 60 * 24)
            return results
        except Exception:  # pragma: no cover - external API dependent
            return []

    def _cache_key(self, query: str, max_results: int, include_raw_content: bool) -> str:
        raw = f"{query}|{max_results}|{include_raw_content}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
