"""
Kashf Backend — Forum & Community Scrapers
Covers: Reddit, StackOverflow, Medium, HackerNews.
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, ScraperResult


# ── Reddit ────────────────────────────────────────────────────────────


class RedditScraper(BaseScraper):
    platform_name = "Reddit"
    base_url = "https://www.reddit.com"
    risk_category = "REPUTATIONAL"

    async def check(self, query: str, query_type: str) -> ScraperResult:
        if query_type == "email":
            return self._not_found()

        # Use the JSON endpoint for cleaner data
        url = f"{self.base_url}/user/{query}/about.json"
        resp = await self._http_get(url)
        if resp and resp.status_code == 200:
            data = resp.json()
            user_data = data.get("data", {})
            if user_data and not user_data.get("is_suspended", False):
                profile_url = f"{self.base_url}/user/{query}"
                return self._ok(profile_url, {
                    "username": user_data.get("name", query),
                    "karma_total": user_data.get("total_karma", 0),
                    "link_karma": user_data.get("link_karma", 0),
                    "comment_karma": user_data.get("comment_karma", 0),
                    "account_created_utc": user_data.get("created_utc", 0),
                    "has_verified_email": user_data.get("has_verified_email", False),
                    "icon": user_data.get("icon_img", ""),
                })
        return self._not_found()


# ── StackOverflow ─────────────────────────────────────────────────────


class StackOverflowScraper(BaseScraper):
    platform_name = "StackOverflow"
    base_url = "https://api.stackexchange.com/2.3"
    risk_category = "REPUTATIONAL"

    async def check(self, query: str, query_type: str) -> ScraperResult:
        if query_type == "email":
            return self._not_found()

        # Search by display name via the StackExchange API
        url = f"{self.base_url}/users"
        params = {
            "inname": query,
            "site": "stackoverflow",
            "pagesize": 5,
            "order": "desc",
            "sort": "reputation",
        }
        resp = await self._http_get(url, params=params)
        if resp and resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            # Look for an exact or close username match
            for user in items:
                display = user.get("display_name", "").lower()
                if display == query.lower() or query.lower() in display:
                    profile_url = user.get("link", f"https://stackoverflow.com/users/{user.get('user_id', '')}")
                    return self._ok(profile_url, {
                        "username": user.get("display_name", query),
                        "reputation": user.get("reputation", 0),
                        "badges_gold": user.get("badge_counts", {}).get("gold", 0),
                        "badges_silver": user.get("badge_counts", {}).get("silver", 0),
                        "badges_bronze": user.get("badge_counts", {}).get("bronze", 0),
                        "avatar": user.get("profile_image", ""),
                        "location": user.get("location", ""),
                    })
        return self._not_found()


# ── Medium ────────────────────────────────────────────────────────────


class MediumScraper(BaseScraper):
    platform_name = "Medium"
    base_url = "https://medium.com"
    risk_category = "REPUTATIONAL"

    async def check(self, query: str, query_type: str) -> ScraperResult:
        if query_type == "email":
            return self._not_found()

        url = f"{self.base_url}/@{query}"
        resp = await self._http_get(url)
        if resp and resp.status_code == 200 and "Page not found" not in resp.text:
            soup = BeautifulSoup(resp.text, "lxml")
            title = soup.find("title")
            name = title.get_text(strip=True).replace(" – Medium", "") if title else query
            meta_desc = soup.find("meta", attrs={"name": "description"})
            bio = meta_desc["content"] if meta_desc and meta_desc.get("content") else ""
            return self._ok(url, {
                "username": query,
                "display_name": name,
                "bio": bio,
            })
        return self._not_found()


# ── Hacker News ───────────────────────────────────────────────────────


class HackerNewsScraper(BaseScraper):
    platform_name = "HackerNews"
    base_url = "https://hacker-news.firebaseio.com/v0"
    risk_category = "REPUTATIONAL"

    async def check(self, query: str, query_type: str) -> ScraperResult:
        if query_type == "email":
            return self._not_found()

        url = f"{self.base_url}/user/{query}.json"
        resp = await self._http_get(url)
        if resp and resp.status_code == 200:
            data = resp.json()
            if data and data.get("id"):
                profile_url = f"https://news.ycombinator.com/user?id={query}"
                return self._ok(profile_url, {
                    "username": data.get("id", query),
                    "karma": data.get("karma", 0),
                    "about": data.get("about", ""),
                    "created": data.get("created", 0),
                })
        return self._not_found()
