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
            return self._not_found()

        url = f"{self.base_url}/{query}"
        resp = await self._http_get(url)
        if resp is None:
            return self._error("Request failed")
        if self._is_auth_wall(resp):
            return self._error("Login wall — Facebook profile requires authentication")
        if resp.status_code == 200 and "page not found" not in resp.text.lower():
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
        if resp is None:
            return self._error("Request failed")
        if resp.status_code == 404:
            return self._not_found()
        if self._is_auth_wall(resp):
            return self._error("Login wall — Instagram profile verification requires authentication")
        if resp.status_code == 200 and "Page Not Found" not in resp.text:
            soup = BeautifulSoup(resp.text, "lxml")
            og_image = soup.find("meta", attrs={"property": "og:image"})
            meta_desc = soup.find("meta", attrs={"property": "og:description"})
            if og_image or meta_desc:
                description = meta_desc["content"] if meta_desc and meta_desc.get("content") else ""
                return self._ok(url, {"username": query, "bio_preview": description})
            return self._error("Bot protection — JavaScript rendering required")
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
        if resp is None:
            return self._error("Request failed")
        if self._is_auth_wall(resp):
            return self._error("Login wall — Twitter/X profile verification requires authentication")
        if resp.status_code == 200 and "This account doesn" not in resp.text:
            soup = BeautifulSoup(resp.text, "lxml")
            title = soup.find("title")
            display = title.get_text(strip=True) if title else ""
            # Generic page title means we got the JS shell, not real profile data
            if display.lower() not in ("x", "twitter", "twitter / x", "x / twitter", ""):
                return self._ok(url, {"username": query, "display_name": display})
            return self._error("Bot protection — Twitter/X blocks automated profile checks")
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
        if resp is None:
            return self._error("Request failed")
        if self._is_auth_wall(resp):
            return self._error("Bot protection detected — TikTok blocks automated checks")
        sample = resp.text[:3000].lower()
        if "captcha" in sample or "verify" in sample:
            return self._error("Bot protection detected — TikTok requires CAPTCHA verification")
        if resp.status_code == 200 and "Couldn't find this account" not in resp.text:
            soup = BeautifulSoup(resp.text, "lxml")
            title = soup.find("title")
            name = title.get_text(strip=True) if title else ""
            if name.lower() not in ("tiktok", ""):
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

        # story.snapchat.com serves SEO-friendly profile pages
        story_url = f"https://story.snapchat.com/@{query}"
        resp = await self._http_get(story_url)
        if resp and resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "lxml")
            og_title = soup.find("meta", attrs={"property": "og:title"})
            title_text = og_title.get("content", "") if og_title else ""
            if title_text and "page not found" not in title_text.lower():
                return self._ok(story_url, {"username": query, "display_name": title_text})

        # Fallback: add page
        add_url = f"https://www.snapchat.com/add/{query}"
        resp2 = await self._http_get(add_url)
        if resp2 and resp2.status_code == 200 and "add_web_not_found" not in resp2.text.lower():
            return self._ok(add_url, {"username": query})
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
        if resp is None:
            return self._error("Request failed")
        if self._is_auth_wall(resp):
            return self._error("Login wall — Pinterest profile requires authentication")
        if resp.status_code == 200 and "Sorry, that page" not in resp.text:
            soup = BeautifulSoup(resp.text, "lxml")
            title = soup.find("title")
            name = title.get_text(strip=True) if title else query
            return self._ok(url, {"username": query, "display_name": name})
        return self._not_found()
