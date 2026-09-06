import time
from typing import Any

import httpx

from app.core.config import settings


class NewsProvider:
    """
    GNews-backed news provider with:

    - in-memory caching
    - daily request safety limit
    - retry handling
    - stale-cache fallback
    - freshness labels
    - last-request tracking

    The API key never leaves the backend.
    """

    GNEWS_URL = "https://gnews.io/api/v4/search"

    def __init__(self) -> None:
        # key -> (timestamp, payload)
        self.cache: dict[str, tuple[float, dict[str, Any]]] = {}

        # Number of actual GNews HTTP requests made by this
        # backend process today.
        self.daily_request_count = 0

        # Unix timestamp representing the day for the counter.
        self.request_day = self._current_day()

        # Last actual GNews request timestamp.
        self.last_called_at: float | None = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _current_day() -> int:
        return int(time.time() // 86400)

    def _reset_daily_counter_if_needed(self) -> None:
        current_day = self._current_day()

        if current_day != self.request_day:
            self.request_day = current_day
            self.daily_request_count = 0

    def _cache_key(self, query: str, limit: int) -> str:
        """
        Include all parameters that affect the response.

        This avoids accidentally returning a cached response generated
        with a different article limit.
        """
        normalized_query = query.strip().lower()
        normalized_limit = min(max(limit, 1), 10)

        return f"{normalized_query}|limit={normalized_limit}"

    def _get_cached(
        self,
        key: str,
    ) -> dict[str, Any] | None:
        cached = self.cache.get(key)

        if not cached:
            return None

        timestamp, payload = cached

        age_seconds = time.time() - timestamp
        max_age_seconds = settings.news_cache_minutes * 60

        if age_seconds < max_age_seconds:
            result = dict(payload)
            result["freshness"] = "cached"
            result["cache_age_seconds"] = int(age_seconds)
            return result

        return None

    def _get_stale_cached(
        self,
        key: str,
    ) -> dict[str, Any] | None:
        """
        Return expired cached data if available.

        This means a temporary GNews outage does not make the
        application suddenly show an empty news section.
        """
        cached = self.cache.get(key)

        if not cached:
            return None

        timestamp, payload = cached

        result = dict(payload)
        result["freshness"] = "stale"
        result["cache_age_seconds"] = int(time.time() - timestamp)

        return result

    def _daily_limit_available(self) -> bool:
        self._reset_daily_counter_if_needed()

        return (
            self.daily_request_count
            < settings.gnews_daily_limit
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        limit: int = 8,
    ) -> dict[str, Any]:

        query = query.strip()

        if not query:
            return {
                "articles": [],
                "freshness": "unavailable",
                "source": "GNews",
                "message": "News search query is empty.",
            }

        limit = min(max(limit, 1), 10)

        key = self._cache_key(query, limit)

        # --------------------------------------------------------------
        # 1. Return fresh cached result
        # --------------------------------------------------------------

        cached = self._get_cached(key)

        if cached is not None:
            return cached

        # --------------------------------------------------------------
        # 2. No API key -> graceful fallback
        # --------------------------------------------------------------

        if not settings.gnews_api_key:
            stale = self._get_stale_cached(key)

            if stale is not None:
                return stale

            return {
                "articles": [],
                "freshness": "unavailable",
                "source": "GNews",
                "message": (
                    "News provider is not configured. "
                    "Using market-data-based explanations."
                ),
            }

        # --------------------------------------------------------------
        # 3. Safety limit
        # --------------------------------------------------------------

        if not self._daily_limit_available():
            stale = self._get_stale_cached(key)

            if stale is not None:
                stale["message"] = (
                    "GNews request limit reached. "
                    "Showing previously cached news."
                )
                return stale

            return {
                "articles": [],
                "freshness": "unavailable",
                "source": "GNews",
                "message": (
                    "GNews daily safety limit reached. "
                    "News is temporarily unavailable."
                ),
            }

        # --------------------------------------------------------------
        # 4. Request GNews
        # --------------------------------------------------------------

        params = {
            "q": query,
            "lang": "en",
            "country": "in",
            "max": limit,
            "apikey": settings.gnews_api_key,
        }

        last_error: Exception | None = None

        for attempt in range(settings.gnews_max_retries + 1):
            try:
                with httpx.Client(
                    timeout=settings.gnews_timeout_seconds
                ) as client:

                    response = client.get(
                        self.GNEWS_URL,
                        params=params,
                    )

                    response.raise_for_status()

                    raw = response.json()

                # Count only successful actual provider calls.
                self.daily_request_count += 1
                self.last_called_at = time.time()

                # ------------------------------------------------------
                # 5. Normalize provider response
                # ------------------------------------------------------

                articles: list[dict[str, Any]] = []

                for article in raw.get("articles", []):
                    source = (
                        (article.get("source") or {}).get("name")
                        or "Unknown source"
                    )

                    articles.append(
                        {
                            "title": article.get("title"),
                            "description": article.get(
                                "description"
                            ),
                            "url": article.get("url"),
                            "image": article.get("image"),
                            "source": source,
                            "published_at": article.get(
                                "publishedAt"
                            ),
                            "verified": True,
                            "provider": "GNews",
                        }
                    )

                payload: dict[str, Any] = {
                    "articles": articles,
                    "freshness": "delayed",
                    "source": "GNews",
                    "request_count_today": (
                        self.daily_request_count
                    ),
                }

                # ------------------------------------------------------
                # 6. Cache successful response
                # ------------------------------------------------------

                self.cache[key] = (
                    time.time(),
                    payload,
                )

                return payload

            except Exception as exc:
                last_error = exc

                # Small backoff before retry.
                if attempt < settings.gnews_max_retries:
                    time.sleep(0.5 * (attempt + 1))

        # --------------------------------------------------------------
        # 7. Provider failed -> stale cache if available
        # --------------------------------------------------------------

        stale = self._get_stale_cached(key)

        if stale is not None:
            stale["message"] = (
                "GNews is temporarily unavailable. "
                "Showing latest cached news."
            )

            return stale

        # --------------------------------------------------------------
        # 8. Complete failure with no cache
        # --------------------------------------------------------------

        return {
            "articles": [],
            "freshness": "error",
            "source": "GNews",
            "message": (
                "News provider request failed; "
                "no headlines were fabricated."
            ),
        }

    # ------------------------------------------------------------------
    # Stock-specific news
    # ------------------------------------------------------------------

    def stock_news(
        self,
        symbol: str,
        company: str,
        limit: int = 8,
    ) -> dict[str, Any]:

        result = self.search(
            f'"{company}" {symbol}',
            limit,
        )

        event_words = (
            "earnings",
            "results",
            "dividend",
            "board",
            "merger",
            "acquisition",
            "split",
            "buyback",
            "order",
            "contract",
            "guidance",
            "appointment",
            "resignation",
            "approval",
            "launch",
            "acquire",
            "stake",
            "funding",
            "investment",
            "deal",
            "agreement",
        )

        for article in result.get("articles", []):
            title = (
                article.get("title") or ""
            ).lower()

            description = (
                article.get("description") or ""
            ).lower()

            combined = f"{title} {description}"

            article["event_type"] = (
                "Corporate event"
                if any(
                    word in combined
                    for word in event_words
                )
                else "Market news"
            )

        return result

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def status(self) -> dict[str, Any]:
        """
        Backend-only diagnostic information.

        Useful later if we want to expose a small admin/debug panel.
        """

        self._reset_daily_counter_if_needed()

        remaining = max(
            settings.gnews_daily_limit
            - self.daily_request_count,
            0,
        )

        return {
            "provider": "GNews",
            "configured": bool(settings.gnews_api_key),
            "requests_today": self.daily_request_count,
            "daily_limit": settings.gnews_daily_limit,
            "remaining": remaining,
            "last_called_at": self.last_called_at,
            "cache_entries": len(self.cache),
            "cache_minutes": settings.news_cache_minutes,
        }


news_provider = NewsProvider()