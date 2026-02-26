"""
Kashf Backend — Public Records & Service Scrapers
Covers: Shodan, Gravatar, Keybase, About.me.
"""

from __future__ import annotations

import hashlib
import logging

from config import settings
from scrapers.base import BaseScraper, ScraperResult

logger = logging.getLogger("kashf.scrapers.public_records")


# ── Shodan ────────────────────────────────────────────────────────────


class ShodanScraper(BaseScraper):
    """
    Checks Shodan for internet-facing services related to the query.
    If email is provided, extracts domain and searches for associated hosts.
    Requires SHODAN_API_KEY for API access.
    """

    platform_name = "Shodan"
    base_url = "https://api.shodan.io"
    risk_category = "INFRASTRUCTURE"

    async def check(self, query: str, query_type: str) -> ScraperResult:
        api_key = settings.SHODAN_API_KEY
        if not api_key:
            logger.warning("[Shodan] No API key configured — skipping")
            return self._error("Shodan API key not configured")

        if query_type == "email":
            # Extract domain from email and search Shodan
            domain = query.split("@")[-1] if "@" in query else None
            if not domain or domain in ("gmail.com", "yahoo.com", "hotmail.com", "outlook.com"):
                return self._not_found()  # Skip common providers
            search_query = f"hostname:{domain}"
        else:
            search_query = query

        url = f"{self.base_url}/shodan/host/search"
        params = {"key": api_key, "query": search_query, "page": 1}

        resp = await self._http_get(url, params=params)
        if resp and resp.status_code == 200:
            data = resp.json()
            total = data.get("total", 0)
            if total > 0:
                matches = data.get("matches", [])[:5]  # Top 5 results
                hosts = []
                for m in matches:
                    hosts.append({
                        "ip": m.get("ip_str", ""),
                        "port": m.get("port", 0),
                        "org": m.get("org", ""),
                        "product": m.get("product", ""),
                        "os": m.get("os", ""),
                    })
                return self._ok(
                    url=f"https://www.shodan.io/search?query={search_query}",
                    data={
                        "total_results": total,
                        "hosts": hosts,
                        "search_query": search_query,
                    },
                )
        return self._not_found()


# ── Gravatar ──────────────────────────────────────────────────────────


class GravatarScraper(BaseScraper):
    """
    Checks Gravatar using the MD5 hash of the email address.
    Returns profile data if a Gravatar profile exists.
    """

    platform_name = "Gravatar"
    base_url = "https://www.gravatar.com"
    risk_category = "REPUTATIONAL"

    async def check(self, query: str, query_type: str) -> ScraperResult:
        if query_type != "email":
            return self._not_found()

        email_hash = hashlib.md5(query.strip().lower().encode()).hexdigest()
        profile_url = f"{self.base_url}/{email_hash}.json"

        resp = await self._http_get(profile_url)
        if resp and resp.status_code == 200:
            data = resp.json()
            entry = data.get("entry", [{}])[0] if data.get("entry") else {}
            return self._ok(
                url=f"{self.base_url}/{email_hash}",
                data={
                    "display_name": entry.get("displayName", ""),
                    "profile_url": entry.get("profileUrl", ""),
                    "avatar": entry.get("thumbnailUrl", ""),
                    "about": entry.get("aboutMe", ""),
                    "location": entry.get("currentLocation", ""),
                    "accounts": [
                        {"name": a.get("shortname", ""), "url": a.get("url", "")}
                        for a in entry.get("accounts", [])
                    ],
                },
            )
        return self._not_found()


# ── Keybase ───────────────────────────────────────────────────────────


class KeybaseScraper(BaseScraper):
    """
    Checks Keybase for user profiles and identity proofs.
    """

    platform_name = "Keybase"
    base_url = "https://keybase.io"
    risk_category = "REPUTATIONAL"

    async def check(self, query: str, query_type: str) -> ScraperResult:
        if query_type == "email":
            return self._not_found()  # Keybase doesn't expose email search publicly

        api_url = f"{self.base_url}/_/api/1.0/user/lookup.json?usernames={query}"
        resp = await self._http_get(api_url)
        if resp and resp.status_code == 200:
            data = resp.json()
            them = data.get("them", [])
            if them and them[0] is not None:
                user = them[0]
                profile = user.get("profile", {})
                proofs = user.get("proofs_summary", {}).get("all", [])
                return self._ok(
                    url=f"{self.base_url}/{query}",
                    data={
                        "username": query,
                        "full_name": profile.get("full_name", ""),
                        "bio": profile.get("bio", ""),
                        "proofs": [
                            {"type": p.get("proof_type", ""), "handle": p.get("nametag", "")}
                            for p in proofs[:10]
                        ],
                    },
                )
        return self._not_found()


# ── About.me ─────────────────────────────────────────────────────────


class AboutMeScraper(BaseScraper):
    """
    Checks About.me for user profiles via URL probing.
    """

    platform_name = "About.me"
    base_url = "https://about.me"
    risk_category = "REPUTATIONAL"

    async def check(self, query: str, query_type: str) -> ScraperResult:
        if query_type == "email":
            return self._not_found()

        url = f"{self.base_url}/{query}"
        resp = await self._http_get(url)
        if resp and resp.status_code == 200 and "page not found" not in resp.text.lower():
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(resp.text, "lxml")
            title = soup.find("title")
            name = title.get_text(strip=True) if title else query
            return self._ok(url, {"username": query, "display_name": name})
        return self._not_found()
