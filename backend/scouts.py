"""
Kashf Backend — Scout Robots
Adapted OSINT gatherers using BeautifulSoup and requests/httpx 
instead of Selenium, optimized for Vercel's Serverless setup.
"""

import asyncio
import logging
from typing import Any, Dict, Optional
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger("kashf.scouts")

class BaseScout:
    """Base scout for serverless OSINT gathering."""
    def __init__(self, platform_name: str, base_url: str, risk_category: str):
        self.platform_name = platform_name
        self.base_url = base_url
        self.risk_category = risk_category
        self.timeout = 10.0 # Fast timeout for serverless

    async def _fetch(self, url: str) -> Optional[str]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    return response.text
        except httpx.RequestError as e:
            logger.warning(f"OSINT Scout failed for {self.platform_name}: {e}")
        return None

    async def check(self, query: str, query_type: str) -> Dict[str, Any]:
        """Override this method in subclasses to define scraping logic."""
        raise NotImplementedError

class SocialScout(BaseScout):
    """Scout for general social media presence."""
    async def check(self, query: str, query_type: str) -> Dict[str, Any]:
        if query_type == "email":
            return {"platform": self.platform_name, "found": False, "risk_category": self.risk_category}

        url = f"{self.base_url}/{query}"
        html = await self._fetch(url)
        if html and "page not found" not in html.lower():
            soup = BeautifulSoup(html, "lxml")
            title = soup.find("title")
            name = title.get_text(strip=True) if title else query
            return {
                "platform": self.platform_name,
                "found": True,
                "url": url,
                "data": {"name": name, "username": query},
                "risk_category": self.risk_category,
                "risk_score": 5.0
            }
        return {"platform": self.platform_name, "found": False, "risk_category": self.risk_category}

class BreachScout(BaseScout):
    """HaveIBeenPwned serverless-friendly scout."""
    def __init__(self, api_key: str = ""):
        super().__init__("HaveIBeenPwned", "https://haveibeenpwned.com/api/v3", "DATA_BREACH")
        self.api_key = api_key

    async def check(self, query: str, query_type: str) -> Dict[str, Any]:
        if query_type != "email" or not self.api_key:
            return {"platform": self.platform_name, "found": False, "risk_category": self.risk_category}

        url = f"{self.base_url}/breachedaccount/{query}?truncateResponse=false"
        headers = {
            "hibp-api-key": self.api_key,
            "User-Agent": "Kashf-Privacy-Dashboard"
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    breaches = resp.json()
                    breach_names = [b.get("Name", "Unknown") for b in breaches]
                    return {
                        "platform": self.platform_name,
                        "found": True,
                        "url": f"https://haveibeenpwned.com/account/{query}",
                        "data": {
                            "breaches_count": len(breaches),
                            "breach_names": breach_names[:20]
                        },
                        "risk_category": self.risk_category,
                        "risk_score": 9.5
                    }
        except httpx.TimeoutException:
            logger.error("HIBP Scout timeout - Vercel function protected.")
        except Exception as e:
            logger.error(f"HIBP Scout error: {e}")

        return {"platform": self.platform_name, "found": False, "risk_category": self.risk_category}

# Define initialized scout robots ready to be imported
twitter_scout = SocialScout("Twitter/X", "https://x.com", "REPUTATIONAL")
instagram_scout = SocialScout("Instagram", "https://www.instagram.com", "STALKING")
github_scout = SocialScout("GitHub", "https://github.com", "REPUTATIONAL")

async def run_scouts(query: str, query_type: str, hibp_api_key: str = "") -> list:
    """Run all scouts concurrently for serverless gathering."""
    scouts = [twitter_scout, instagram_scout, github_scout]
    if hibp_api_key:
        scouts.append(BreachScout(hibp_api_key))
        
    tasks = [scout.check(query, query_type) for scout in scouts]
    results = await asyncio.gather(*tasks)
    return results
