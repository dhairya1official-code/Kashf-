"""
Kashf Backend — Social Media Scrapers
Covers: Facebook, Instagram, Twitter/X, TikTok, Snapchat, Pinterest.
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, ScraperResult


# ── Facebook ──────────────────────────────────────────────────────────


class FacebookScraper(BaseScraper):
    platform_name = "Facebook"
    base_url = "https://www.facebook.com"
    risk_category = "IMPERSONATION"

    async def check(self, query: str, query_type: str) -> ScraperResult:
        if query_type == "email":
            return self._not_found()  # Facebook doesn't expose profiles by email

        url = f"{self.base_url}/{query}"
        resp = await self._http_get(url)
        if resp and resp.status_code == 200 and "page not found" not in resp.text.lower():
            soup = BeautifulSoup(resp.text, "lxml")
            title = soup.find("title")
            name = title.get_text(strip=True) if title else query
            return self._ok(url, {"name": name, "username": query})
        return self._not_found()


# ── Instagram ─────────────────────────────────────────────────────────


class InstagramScraper(BaseScraper):
    platform_name = "Instagram"
    base_url = "https://www.instagram.com"
    risk_category = "STALKING"

    async def check(self, query: str, query_type: str) -> ScraperResult:
        if query_type == "email":
            return self._not_found()

        url = f"{self.base_url}/{query}/"
        resp = await self._http_get(url)
        if resp and resp.status_code == 200 and "Page Not Found" not in resp.text:
            soup = BeautifulSoup(resp.text, "lxml")
            meta_desc = soup.find("meta", attrs={"property": "og:description"})
            description = meta_desc["content"] if meta_desc and meta_desc.get("content") else ""
            return self._ok(url, {"username": query, "bio_preview": description})
        return self._not_found()


# ── Twitter / X ───────────────────────────────────────────────────────


class TwitterScraper(BaseScraper):
    platform_name = "Twitter/X"
    base_url = "https://x.com"
    risk_category = "REPUTATIONAL"

    async def check(self, query: str, query_type: str) -> ScraperResult:
        if query_type == "email":
            return self._not_found()

        url = f"{self.base_url}/{query}"
        resp = await self._http_get(url)
        if resp and resp.status_code == 200 and "This account doesn" not in resp.text:
            soup = BeautifulSoup(resp.text, "lxml")
            title = soup.find("title")
            display = title.get_text(strip=True) if title else query
            return self._ok(url, {"username": query, "display_name": display})
        return self._not_found()


# ── TikTok ────────────────────────────────────────────────────────────


class TikTokScraper(BaseScraper):
    platform_name = "TikTok"
    base_url = "https://www.tiktok.com"
    risk_category = "STALKING"

    async def check(self, query: str, query_type: str) -> ScraperResult:
        if query_type == "email":
            return self._not_found()

        url = f"{self.base_url}/@{query}"
        resp = await self._http_get(url)
        if resp and resp.status_code == 200 and "Couldn't find this account" not in resp.text:
            soup = BeautifulSoup(resp.text, "lxml")
            title = soup.find("title")
            name = title.get_text(strip=True) if title else query
            return self._ok(url, {"username": query, "display_name": name})
        return self._not_found()


# ── Snapchat ──────────────────────────────────────────────────────────


class SnapchatScraper(BaseScraper):
    platform_name = "Snapchat"
    base_url = "https://www.snapchat.com/add"
    risk_category = "STALKING"

    async def check(self, query: str, query_type: str) -> ScraperResult:
        if query_type == "email":
            return self._not_found()

        url = f"{self.base_url}/{query}"
        resp = await self._http_get(url)
        if resp and resp.status_code == 200 and "add_web_not_found" not in resp.text.lower():
            return self._ok(url, {"username": query})
        return self._not_found()


# ── Pinterest ─────────────────────────────────────────────────────────


class PinterestScraper(BaseScraper):
    platform_name = "Pinterest"
    base_url = "https://www.pinterest.com"
    risk_category = "REPUTATIONAL"

    async def check(self, query: str, query_type: str) -> ScraperResult:
        if query_type == "email":
            return self._not_found()

        url = f"{self.base_url}/{query}/"
        resp = await self._http_get(url)
        if resp and resp.status_code == 200 and "Sorry, that page" not in resp.text:
            soup = BeautifulSoup(resp.text, "lxml")
            title = soup.find("title")
            name = title.get_text(strip=True) if title else query
            return self._ok(url, {"username": query, "display_name": name})
        return self._not_found()
