"""
Kashf Backend — Breach Database Scrapers
Covers: HaveIBeenPwned, Dehashed.
"""

from __future__ import annotations

import logging

from config import settings
from scrapers.base import BaseScraper, ScraperResult

logger = logging.getLogger("kashf.scrapers.breach")


# ── HaveIBeenPwned ────────────────────────────────────────────────────


class HIBPScraper(BaseScraper):
    """
    Uses the HaveIBeenPwned API v3 to check email breaches.
    Requires a paid API key set in HIBP_API_KEY.
    Degrades gracefully if no key is configured.
    """

    platform_name = "HaveIBeenPwned"
    base_url = "https://haveibeenpwned.com/api/v3"
    risk_category = "DATA_BREACH"

    async def check(self, query: str, query_type: str) -> ScraperResult:
        if query_type != "email":
            return self._not_found()

        api_key = settings.HIBP_API_KEY
        if not api_key:
            logger.warning("[HIBP] No API key configured — skipping breach check")
            return self._error("HIBP API key not configured")

        url = f"{self.base_url}/breachedaccount/{query}"
        headers = {
            "hibp-api-key": api_key,
            "User-Agent": "Kashf-Privacy-Dashboard",
        }
        params = {"truncateResponse": "false"}

        resp = await self._http_get(url, headers=headers, params=params)

        if resp is None:
            return self._error("HIBP request failed")

        if resp.status_code == 404:
            # No breaches — good news
            return self._not_found()

        if resp.status_code == 200:
            breaches = resp.json()
            breach_names = [b.get("Name", "Unknown") for b in breaches]
            total_pwned = sum(b.get("PwnCount", 0) for b in breaches)
            data_classes = set()
            for b in breaches:
                data_classes.update(b.get("DataClasses", []))

            return self._ok(
                url=f"https://haveibeenpwned.com/account/{query}",
                data={
                    "breaches_count": len(breaches),
                    "breach_names": breach_names[:20],  # Cap at 20
                    "total_records_exposed": total_pwned,
                    "data_types_exposed": sorted(data_classes),
                    "most_recent_breach": breaches[0].get("BreachDate", "") if breaches else "",
                },
            )

        if resp.status_code == 401:
            return self._error("HIBP API key invalid")
        if resp.status_code == 429:
            return self._error("HIBP rate limit exceeded")

        return self._error(f"HIBP returned status {resp.status_code}")


# ── Dehashed ──────────────────────────────────────────────────────────


class DehashedScraper(BaseScraper):
    """
    Checks Dehashed public search to see if an email/username
    appears in known breach datasets.
    """

    platform_name = "Dehashed"
    base_url = "https://www.dehashed.com"
    risk_category = "DATA_BREACH"

    async def check(self, query: str, query_type: str) -> ScraperResult:
        search_param = "email" if query_type == "email" else "username"
        url = f"{self.base_url}/search?query={search_param}:{query}"

        resp = await self._http_get(url)
        if resp and resp.status_code == 200:
            text_lower = resp.text.lower()
            # Check if results were found (page shows count)
            if "no results found" not in text_lower and "entries found" in text_lower:
                return self._ok(url, {
                    "query": query,
                    "query_type": query_type,
                    "source": "dehashed_public_search",
                })
        return self._not_found()
