"""
Kashf Backend — Base Scraper
Abstract base class for all OSINT scrapers.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import httpx

from config import settings

logger = logging.getLogger("kashf.scrapers")


@dataclass
class ScraperResult:
    """Standardized result returned by every scraper."""
    platform: str
    url: str | None = None
    found: bool = False
    data: dict[str, Any] = field(default_factory=dict)
    risk_category: str = ""
    risk_score: float = 0.0
    error: str | None = None


class BaseScraper(ABC):
    """
    Abstract base for all platform scrapers.

    Subclasses must implement:
      - platform_name  (property)
      - base_url       (property)
      - risk_category  (property)
      - check()        (async method)
    """

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    # ── Abstract interface ────────────────────────────────────────────

    @property
    @abstractmethod
    def platform_name(self) -> str: ...

    @property
    @abstractmethod
    def base_url(self) -> str: ...

    @property
    @abstractmethod
    def risk_category(self) -> str: ...

    @abstractmethod
    async def check(self, query: str, query_type: str) -> ScraperResult: ...

    # ── Shared helpers ────────────────────────────────────────────────

    def _random_ua(self) -> str:
        return random.choice(settings.USER_AGENTS)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(settings.SCRAPER_TIMEOUT),
                follow_redirects=True,
                headers={"User-Agent": self._random_ua()},
            )
        return self._client

    async def _http_get(self, url: str, **kwargs: Any) -> httpx.Response | None:
        """Safe GET request that returns None on failure."""
        try:
            client = await self._get_client()
            resp = await client.get(url, **kwargs)
            return resp
        except (httpx.HTTPError, asyncio.TimeoutError) as exc:
            logger.debug(f"[{self.platform_name}] GET {url} failed: {exc}")
            return None

    async def _http_head(self, url: str, **kwargs: Any) -> httpx.Response | None:
        """Safe HEAD request — useful for quick existence checks."""
        try:
            client = await self._get_client()
            resp = await client.head(url, **kwargs)
            return resp
        except (httpx.HTTPError, asyncio.TimeoutError) as exc:
            logger.debug(f"[{self.platform_name}] HEAD {url} failed: {exc}")
            return None

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _ok(self, url: str, data: dict[str, Any] | None = None) -> ScraperResult:
        """Convenience: build a 'found' result."""
        return ScraperResult(
            platform=self.platform_name,
            url=url,
            found=True,
            data=data or {},
            risk_category=self.risk_category,
        )

    def _not_found(self) -> ScraperResult:
        """Convenience: build a 'not found' result."""
        return ScraperResult(
            platform=self.platform_name,
            found=False,
            risk_category=self.risk_category,
        )

    def _error(self, msg: str) -> ScraperResult:
        """Convenience: build an error result."""
        return ScraperResult(
            platform=self.platform_name,
            found=False,
            error=msg,
            risk_category=self.risk_category,
        )
