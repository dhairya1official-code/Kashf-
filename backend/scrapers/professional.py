"""
Kashf Backend — Professional Platform Scrapers
Covers: LinkedIn, GitHub, GitLab, Behance.
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, ScraperResult


# ── LinkedIn ──────────────────────────────────────────────────────────


class LinkedInScraper(BaseScraper):
    platform_name = "LinkedIn"
    base_url = "https://www.linkedin.com/in"
    risk_category = "PHISHING"

    async def check(self, query: str, query_type: str) -> ScraperResult:
        if query_type == "email":
            return self._not_found()

        url = f"{self.base_url}/{query}"
        resp = await self._http_get(url)
        if resp and resp.status_code == 200 and "page-not-found" not in resp.text.lower():
            soup = BeautifulSoup(resp.text, "lxml")
            title = soup.find("title")
            name = title.get_text(strip=True).replace(" | LinkedIn", "") if title else query
            meta_desc = soup.find("meta", attrs={"name": "description"})
            headline = meta_desc["content"] if meta_desc and meta_desc.get("content") else ""
            return self._ok(url, {
                "username": query,
                "name": name,
                "headline": headline,
            })
        return self._not_found()


# ── GitHub ────────────────────────────────────────────────────────────


class GitHubScraper(BaseScraper):
    platform_name = "GitHub"
    base_url = "https://api.github.com/users"
    risk_category = "REPUTATIONAL"

    async def check(self, query: str, query_type: str) -> ScraperResult:
        # GitHub API supports searching by username; for email we search events
        if query_type == "email":
            # Search commits for the email
            search_url = f"https://api.github.com/search/users?q={query}+in:email"
            resp = await self._http_get(search_url)
            if resp and resp.status_code == 200:
                data = resp.json()
                if data.get("total_count", 0) > 0:
                    user = data["items"][0]
                    profile_url = user.get("html_url", "")
                    return self._ok(profile_url, {
                        "username": user.get("login", ""),
                        "avatar": user.get("avatar_url", ""),
                    })
            return self._not_found()

        # Username lookup
        url = f"{self.base_url}/{query}"
        resp = await self._http_get(url)
        if resp and resp.status_code == 200:
            data = resp.json()
            profile_url = data.get("html_url", f"https://github.com/{query}")
            return self._ok(profile_url, {
                "username": data.get("login", query),
                "name": data.get("name", ""),
                "bio": data.get("bio", ""),
                "public_repos": data.get("public_repos", 0),
                "followers": data.get("followers", 0),
                "avatar": data.get("avatar_url", ""),
                "company": data.get("company", ""),
                "location": data.get("location", ""),
                "blog": data.get("blog", ""),
                "created_at": data.get("created_at", ""),
            })
        return self._not_found()


# ── GitLab ────────────────────────────────────────────────────────────


class GitLabScraper(BaseScraper):
    platform_name = "GitLab"
    base_url = "https://gitlab.com"
    risk_category = "REPUTATIONAL"

    async def check(self, query: str, query_type: str) -> ScraperResult:
        if query_type == "email":
            return self._not_found()

        api_url = f"{self.base_url}/api/v4/users?username={query}"
        resp = await self._http_get(api_url)
        if resp and resp.status_code == 200:
            users = resp.json()
            if users and len(users) > 0:
                user = users[0]
                profile_url = user.get("web_url", f"{self.base_url}/{query}")
                return self._ok(profile_url, {
                    "username": user.get("username", query),
                    "name": user.get("name", ""),
                    "avatar": user.get("avatar_url", ""),
                    "state": user.get("state", ""),
                })
        return self._not_found()


# ── Behance ───────────────────────────────────────────────────────────


class BehanceScraper(BaseScraper):
    platform_name = "Behance"
    base_url = "https://www.behance.net"
    risk_category = "REPUTATIONAL"

    async def check(self, query: str, query_type: str) -> ScraperResult:
        if query_type == "email":
            return self._not_found()

        url = f"{self.base_url}/{query}"
        resp = await self._http_get(url)
        if resp and resp.status_code == 200 and "Page Not Found" not in resp.text:
            soup = BeautifulSoup(resp.text, "lxml")
            title = soup.find("title")
            name = title.get_text(strip=True) if title else query
            return self._ok(url, {"username": query, "display_name": name})
        return self._not_found()
